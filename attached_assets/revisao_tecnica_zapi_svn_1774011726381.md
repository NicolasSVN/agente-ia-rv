# Revisão Técnica — Integração Z-API · SVN Renda Variável
> Documento gerado para uso interno do time de desenvolvimento.  
> Autor: Stevan (IA Interna — Área de Renda Variável SVN)  
> Base: Plano Replit + Artigo Z-API (março/2026) + Análise de boas práticas

---

## Índice

1. [Resumo de Prioridade Recomendada](#1-resumo-de-prioridade-recomendada)
2. [O que o Replit acertou — e deve ser implementado](#2-o-que-o-replit-acertou--e-deve-ser-implementado)
3. [O que precisa de nuance antes de implementar](#3-o-que-precisa-de-nuance-antes-de-implementar)
4. [O que ficou de fora do plano Replit](#4-o-que-ficou-de-fora-do-plano-replit)
5. [Segurança extra — padrões observados em outras instâncias Z-API](#5-segurança-extra--padrões-observados-em-outras-instâncias-z-api)
6. [Mudanças perigosas — o que pode crashar a aplicação](#6-mudanças-perigosas--o-que-pode-crashar-a-aplicação)
7. [Checklist de entrega — como nos dar a devolutiva](#7-checklist-de-entrega--como-nos-dar-a-devolutiva)

---

## 1. Resumo de Prioridade Recomendada

| Prioridade | Item | Risco atual | Complexidade |
|---|---|---|---|
| 🔴 **Imediato** | Segurança do Webhook (autenticação de origem) | Injeção de mensagens falsas na plataforma | Baixa |
| 🔴 **Imediato** | Idempotência no envio (`messageId`) | Mensagem duplicada ao cliente final | Baixa |
| 🟡 **Curto prazo** | Retry com backoff exponencial | Falhas silenciosas em campanhas sem aviso ao assessor | Média |
| 🟡 **Curto prazo** | Health check real da instância Z-API | Instância desconectada reportada como "ok" | Média |
| 🟠 **Médio prazo** | Status de entrega no frontend | Assessor sem visibilidade real do que foi entregue/lido | Alta |
| 🟠 **Médio prazo** | Rate limiting em campanhas | Risco de banimento da instância por disparo sem cadência | Média |
| ⚪ **Quando escalar** | Semáforo de concorrência (áudio/imagem) | Saturação do worker com volume alto de mídia | Média |
| ⚪ **Quando escalar** | Fila externa (Redis + workers) | Substitui o semáforo quando o volume exigir | Alta |

---

## 2. O que o Replit acertou — e deve ser implementado

### 2.1 🔴 Idempotência no envio de saída (P0)

**Por que é crítico:** Em mensageria financeira, o cliente receber duas vezes a mesma mensagem de um assessor é um problema de imagem real e pode gerar confusão em comunicados de produto. A Z-API aceita o campo `messageId` exatamente para isso.

**Arquivo:** `services/whatsapp_client.py`, linhas 110–126

**Situação atual:**
```python
# SEM controle de idempotência
payload = {
    "phone": self._normalize_phone(to),
    "message": message
    # ← nenhum campo de identificação único
}
```

**Implementação recomendada:**
```python
import uuid

async def send_text(self, to, message, delay_message=0, delay_typing=0, dedupe_key=None) -> dict:
    if dedupe_key is None:
        dedupe_key = str(uuid.uuid4())

    payload = {
        "phone": self._normalize_phone(to),
        "message": message,
        "messageId": dedupe_key   # Z-API usa este campo para deduplicação nativa
    }
```

**Tabela Outbox no banco (models.py):**
```python
class OutboxMessage(Base):
    __tablename__ = "outbox_messages"
    id          = Column(Integer, primary_key=True)
    dedupe_key  = Column(String, unique=True, nullable=False)  # UNIQUE = anti-duplicação
    phone       = Column(String, nullable=False)
    message_type = Column(String, default="text")
    status      = Column(String, default="PENDING")  # PENDING | SENT | FAILED
    zaap_id     = Column(String, nullable=True)       # ID retornado pelo Z-API
    created_at  = Column(DateTime, default=datetime.utcnow)
    sent_at     = Column(DateTime, nullable=True)
```

**Fluxo de uso:**
1. Antes de enviar: `INSERT INTO outbox_messages (dedupe_key, ...)` — se já existe com status `SENT`, abortar.
2. Após envio bem-sucedido: `UPDATE status='SENT', zaap_id=<retorno Z-API>`.
3. Em retry: reutilizar o mesmo `dedupe_key` — o Z-API ignora duplicata, o banco também.

---

### 2.2 🔴 Segurança do Webhook — autenticação de origem (BÔNUS → P0)

> ⚠️ **Este item foi classificado como "bônus" no plano Replit, mas deve ser tratado como P0 junto com idempotência.** Num ambiente financeiro regulado, um endpoint de webhook sem autenticação é uma superfície de ataque real.

**Arquivo:** `api/endpoints/whatsapp_webhook.py`

**Problema:** Qualquer origem pode fazer `POST /api/webhook/zapi` e injetar mensagens falsas no histórico de conversas. Não há validação do header `Client-Token`.

**Implementação recomendada:**
```python
from fastapi import Request, HTTPException
from core.config import settings

ZAPI_WEBHOOK_SECRET = settings.ZAPI_CLIENT_TOKEN  # token já existente no projeto

@router.post("/zapi")
async def zapi_webhook(
    request: Request,
    payload: Dict[str, Any] = Body(...),
):
    client_token = (
        request.headers.get("client-token") or
        request.headers.get("Client-Token")
    )
    if client_token != ZAPI_WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Webhook não autorizado")

    # ... resto do handler sem alteração
```

**Por que usar o token já existente:** A Z-API envia o `Client-Token` no header de cada webhook. Não é necessário gerar um secret novo — o token já configurado serve como assinatura de origem.

---

### 2.3 🟠 Validação de tamanho de mídia (P3)

**Arquivo:** `services/whatsapp_client.py`, linhas 248–280

**Problema:** PDFs e imagens são enviados sem verificação de tamanho. O WhatsApp rejeita silenciosamente — o Z-API retorna erro, mas a aplicação não informa o assessor.

**Limites do WhatsApp via Z-API:**
- Documentos/PDF: **16 MB**
- Imagens: **5 MB**
- Áudio: **16 MB**

**Implementação recomendada:**
```python
WHATSAPP_DOC_LIMIT_MB  = 16
WHATSAPP_IMG_LIMIT_MB  = 5

async def _check_url_file_size(self, url: str, limit_mb: int) -> tuple[bool, int]:
    """HEAD request primeiro; fallback para streaming parcial."""
    async with httpx.AsyncClient() as client:
        try:
            head = await client.head(url, timeout=5)
            content_length = head.headers.get("content-length")
        except Exception:
            content_length = None

        if not content_length:
            # Fallback: lê só os primeiros bytes para pegar o header
            async with client.stream("GET", url, timeout=10) as response:
                content_length = response.headers.get("content-length")

        if content_length:
            size_mb = int(content_length) / (1024 * 1024)
            return size_mb <= limit_mb, round(size_mb, 1)

    return True, 0  # se não conseguir checar, tenta enviar (fail open)

async def send_document(self, to, document_url, filename="", caption=""):
    ok, size_mb = await self._check_url_file_size(document_url, WHATSAPP_DOC_LIMIT_MB)
    if not ok:
        logger.error(f"[ZAPI] Documento '{filename}' excede limite ({size_mb}MB > {WHATSAPP_DOC_LIMIT_MB}MB)")
        return {
            "success": False,
            "error": f"Arquivo excede o limite do WhatsApp ({size_mb}MB > {WHATSAPP_DOC_LIMIT_MB}MB)",
            "error_code": "FILE_TOO_LARGE"
        }
    # ... envio normal
```

**Frontend — aviso antes de enviar (tela de materiais):**
```javascript
function validateFileBeforeWhatsApp(fileSizeBytes, fileType = "document") {
    const limits = { document: 16, image: 5, audio: 16 };
    const limit  = limits[fileType] ?? 16;
    const sizeMB = fileSizeBytes / (1024 * 1024);

    if (sizeMB > limit) {
        showWarning(
            `Este arquivo tem ${sizeMB.toFixed(1)}MB e pode não ser entregue pelo WhatsApp ` +
            `(limite: ${limit}MB). Considere comprimir ou enviar por outro canal.`
        );
        return false;
    }
    return true;
}
```

---

## 3. O que precisa de nuance antes de implementar

### 3.1 🟡 Semáforo de concorrência — atenção ao modelo de deploy (P1)

**Arquivo:** `api/endpoints/whatsapp_webhook.py`, linhas 1415–1445

O plano Replit propõe um `asyncio.Semaphore` global para limitar processamento paralelo de áudio/imagem. A solução é válida, **mas com uma ressalva importante:**

> ⚠️ `asyncio.Semaphore` é **por processo**. Se a aplicação rodar com múltiplos workers (ex: `gunicorn -w 4`), cada worker tem seu próprio semáforo independente — o limite de 3 transcrições simultâneas vira 3 × N workers.

**Antes de implementar, verifique:**
```bash
# Como a aplicação sobe em produção?
# Exemplo Gunicorn multi-worker:
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# vs. Uvicorn single-process:
uvicorn app.main:app --workers 1
```

**Se for single-process (uvicorn simples), o semáforo funciona perfeitamente:**
```python
import asyncio

_audio_semaphore = asyncio.Semaphore(3)
_image_semaphore = asyncio.Semaphore(5)

async def process_audio_message_limited(phone, media_url, db, message_record, conversation):
    async with _audio_semaphore:
        await process_audio_message(phone, media_url, db, message_record, conversation)

# No handler:
elif message_type == MessageType.AUDIO.value:
    background_tasks.add_task(
        process_audio_message_limited,
        phone, media_url, db, message_record, conversation
    )
```

**Se for multi-worker**, o semáforo não resolve — a solução correta é Redis + Celery/ARQ (anotar como dívida técnica e implementar quando o volume justificar).

---

### 3.2 🟡 Health check real — cuidado com cascata de chamadas (P2)

**Arquivo:** `services/dependency_check.py`, linhas 84–91

O plano propõe um loop periódico no backend + polling do frontend a cada 60s. A estrutura está certa, mas há um detalhe que pode gerar problema em produção:

> ⚠️ O endpoint `/api/integrations/zapi/health` que o frontend consulta a cada 60s **não deve fazer uma nova chamada à Z-API a cada request**. Deve retornar apenas o **cache** atualizado pelo loop interno.

**Implementação correta:**
```python
# Em algum módulo de estado global (ex: core/state.py)
_zapi_status_cache: dict = {"status": "unknown", "checked_at": None}

# Loop periódico — roda UMA VEZ na subida da app (lifespan)
async def _zapi_health_loop():
    while True:
        try:
            result = await check_zapi_connectivity()   # chama Z-API de verdade
            _zapi_status_cache.update(result)
            if result["status"] == "disconnected":
                logger.error("[ZAPI] Instância desconectada — assessores não receberão mensagens!")
        except Exception as e:
            logger.error(f"[ZAPI] Erro no health loop: {e}")
        await asyncio.sleep(300)  # 5 minutos entre verificações reais

# Endpoint público — só lê o cache, nunca chama Z-API diretamente
@router.get("/zapi/health")
async def zapi_health():
    return _zapi_status_cache  # resposta instantânea, sem I/O externo
```

**Erro a evitar:**
```python
# ❌ NUNCA faça isso no endpoint público:
@router.get("/zapi/health")
async def zapi_health():
    return await check_zapi_connectivity()  # cada request do frontend vira uma chamada à Z-API
```

Com 10 assessores com a tela aberta, isso seriam 10 chamadas por minuto à Z-API — desnecessário e arriscado para a instância.

---

## 4. O que ficou de fora do plano Replit

### 4.1 🟡 Retry com backoff exponencial — falhas silenciosas

**Por que é crítico para a SVN:** Se a instância Z-API tiver instabilidade momentânea (comum em fins de semana, fora do horário comercial), o envio falha silenciosamente e o assessor não sabe. O cliente não recebe. Ninguém descobre até alguém reclamar.

**Onde implementar:** `services/whatsapp_client.py` — método `send_text` e demais métodos de envio.

**Padrão recomendado:**
```python
import asyncio
import httpx

MAX_RETRIES = 3
RETRY_DELAYS = [1, 3, 7]  # segundos — backoff crescente

async def _send_with_retry(self, url: str, payload: dict, headers: dict) -> dict:
    last_exception = None

    for attempt, delay in enumerate(RETRY_DELAYS, start=1):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=30.0)

            # 4xx = erro no payload/autenticação — NÃO retentar
            if response.status_code >= 400 and response.status_code < 500:
                logger.error(f"[ZAPI] Erro {response.status_code} — sem retry: {response.text}")
                return {"success": False, "error": response.text, "status_code": response.status_code}

            # 2xx = sucesso
            if response.status_code < 300:
                return response.json()

        except (httpx.TimeoutException, httpx.ConnectError) as e:
            last_exception = e
            logger.warning(f"[ZAPI] Tentativa {attempt}/{MAX_RETRIES} falhou: {e}. Aguardando {delay}s...")
            await asyncio.sleep(delay)

    logger.error(f"[ZAPI] Todas as tentativas falharam. Último erro: {last_exception}")
    return {"success": False, "error": str(last_exception), "error_code": "MAX_RETRIES_EXCEEDED"}
```

> **Regra de ouro:** Retry apenas em erros transitórios (timeout, 5xx). Nunca em 4xx — esses indicam problema no payload que retry não vai resolver, e podem consumir cota desnecessariamente.

---

### 4.2 🟠 Status de entrega no frontend — lacuna de UX

**Por que importa:** Hoje o assessor só sabe se a mensagem "saiu" do sistema. Não sabe se foi entregue ao WhatsApp do cliente, nem se foi lida. Para um ambiente de atendimento de alta qualidade, isso é uma lacuna grande.

A Z-API envia webhooks de status (`message-status`) com os seguintes estados:
- `SENT` — aceito pela Z-API
- `DELIVERED` — entregue ao dispositivo do cliente
- `READ` — lido pelo cliente
- `FAILED` — falha definitiva

**Onde conectar:**
1. No handler de webhook (`api/endpoints/whatsapp_webhook.py`), capturar eventos de tipo `message-status`.
2. Atualizar a tabela `OutboxMessage` (criada no P0) com o status atual.
3. Frontend: exibir ícones de status por mensagem (✓ enviado, ✓✓ entregue, ✓✓ azul lido).

```python
# No webhook handler — adicionar tratamento de status de entrega
if payload.get("type") == "DeliveryCallback":
    message_id = payload.get("messageId") or payload.get("id")
    status     = payload.get("status")  # SENT | DELIVERED | READ | FAILED

    if message_id and status:
        await update_message_delivery_status(db, message_id, status)
```

---

### 4.3 🟠 Rate limiting em campanhas — risco de banimento da instância

**Por que importa:** Disparar centenas de mensagens sem cadência é um dos principais motivos de banimento de instâncias WhatsApp. A Z-API não protege automaticamente contra isso — é responsabilidade da aplicação.

**Onde verificar:** módulo de campanhas (provavelmente `services/` ou `api/endpoints/`).

**Implementação recomendada — delay entre envios:**
```python
import asyncio

CAMPAIGN_DELAY_SECONDS = 1.5  # mínimo recomendado entre mensagens em campanha

async def send_campaign_messages(messages: list[dict]):
    for i, msg in enumerate(messages):
        try:
            await zapi_client.send_text(msg["phone"], msg["text"])
            logger.info(f"[CAMPAIGN] Enviado {i+1}/{len(messages)} para {msg['phone']}")
        except Exception as e:
            logger.error(f"[CAMPAIGN] Falha ao enviar para {msg['phone']}: {e}")

        # Delay entre mensagens — evita banimento
        if i < len(messages) - 1:
            await asyncio.sleep(CAMPAIGN_DELAY_SECONDS)
```

> **Referência Z-API:** Para listas grandes (>100 contatos), considerar delay de 2–3s entre mensagens e evitar horários fora do comercial (risco maior de marcação como spam).

---

### 4.4 ⚪ Logs estruturados para auditoria — dívida técnica importante

**Por que mencionar:** A SVN opera num ambiente de mercado financeiro. Rastreabilidade de comunicações pode ser exigida por compliance ou auditoria interna. Logs estruturados com `assessor_id`, `phone`, `message_type`, `timestamp` e `dedupe_key` são a base disso.

**Não precisa ser implementado agora**, mas o Outbox criado no P0 já resolve parcialmente. Complemento sugerido:

```python
# Ao registrar mensagem enviada
logger.info(
    "[MSG_SENT]",
    extra={
        "assessor_id": current_user.id,
        "phone": normalized_phone,
        "message_type": "text",
        "dedupe_key": dedupe_key,
        "zaap_id": response.get("zaapId"),
        "timestamp": datetime.utcnow().isoformat()
    }
)
```

---

## 5. Segurança extra — padrões observados em outras instâncias Z-API

Além dos itens do plano Replit, estas práticas são documentadas e observadas em integrações Z-API em produção:

### 5.1 — Nunca expor o `Client-Token` no frontend

O `Client-Token` da Z-API **jamais deve aparecer no JavaScript do frontend ou em respostas de API públicas**. Ele deve existir apenas em variáveis de ambiente do servidor.

```python
# ✅ CERTO — token só no backend
ZAPI_CLIENT_TOKEN = os.getenv("ZAPI_CLIENT_TOKEN")

# ❌ ERRADO — jamais retornar em endpoint acessível ao browser
@router.get("/config")
def get_config():
    return {"zapi_token": settings.ZAPI_CLIENT_TOKEN}  # NUNCA
```

### 5.2 — Validação de formato de telefone antes do envio

Números inválidos consomem requisições e podem retornar erros que parecem instabilidade da Z-API. Validar antes.

```python
import re

def validate_phone_br(phone: str) -> bool:
    """Valida telefone brasileiro: 55 + DDD + número (com ou sem 9)."""
    cleaned = re.sub(r'\D', '', phone)
    # Formato: 55 + 2 dígitos DDD + 8 ou 9 dígitos
    return bool(re.match(r'^55\d{2}[89]\d{7,8}$', cleaned))

# Uso antes de qualquer envio
if not validate_phone_br(to):
    logger.warning(f"[ZAPI] Número inválido ignorado: {to}")
    return {"success": False, "error": "Número inválido", "error_code": "INVALID_PHONE"}
```

### 5.3 — IP allowlist no webhook (se infraestrutura permitir)

A Z-API opera a partir de um conjunto conhecido de IPs. Se o ambiente de produção da SVN permitir regras de firewall ou middleware de IP, adicionar um allowlist dos IPs Z-API é uma segunda camada além da validação do token.

> Consultar a documentação atual da Z-API para a lista de IPs de saída dos webhooks — pode variar por plano/região.

### 5.4 — Webhook idempotente no recebimento

Assim como o envio pode ser duplicado, o **recebimento também pode**. A Z-API pode reenviar um webhook se não receber resposta 200 em tempo hábil.

```python
# Tabela simples para deduplicar webhooks recebidos
class ReceivedWebhook(Base):
    __tablename__ = "received_webhooks"
    id         = Column(Integer, primary_key=True)
    event_id   = Column(String, unique=True, nullable=False)  # ID do evento Z-API
    received_at = Column(DateTime, default=datetime.utcnow)

# No handler:
event_id = payload.get("messageId") or payload.get("id")
if event_id:
    existing = db.query(ReceivedWebhook).filter_by(event_id=event_id).first()
    if existing:
        return {"status": "duplicate_ignored"}  # retorna 200 para não gerar retry
    db.add(ReceivedWebhook(event_id=event_id))
    db.commit()
```

### 5.5 — Timeout agressivo no health check

O check de conectividade real da Z-API deve ter timeout curto — evitar que um health check travado bloqueie o loop do servidor.

```python
async def check_zapi_connectivity() -> dict:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:  # máximo 5s
            response = await client.get(
                f"https://api.z-api.io/instances/{settings.ZAPI_INSTANCE_ID}/token/{settings.ZAPI_TOKEN}/status",
                headers={"Client-Token": settings.ZAPI_CLIENT_TOKEN}
            )
            data = response.json()
            return {
                "status": "connected" if data.get("connected") else "disconnected",
                "checked_at": datetime.utcnow().isoformat()
            }
    except httpx.TimeoutException:
        return {"status": "timeout", "checked_at": datetime.utcnow().isoformat()}
    except Exception as e:
        return {"status": "error", "detail": str(e), "checked_at": datetime.utcnow().isoformat()}
```

---

## 6. Mudanças perigosas — o que pode crashar a aplicação

> Leia esta seção **antes de qualquer commit**. São os pontos que, se implementados sem cuidado, podem derrubar a aplicação em produção.

### ⛔ 6.1 — Migration de banco sem teste local primeiro

A criação das tabelas `OutboxMessage` e `ReceivedWebhook` requer migration do Alembic (ou equivalente). **Nunca rodar `alembic upgrade head` direto em produção sem antes:**

```bash
# 1. Gerar a migration
alembic revision --autogenerate -m "add_outbox_and_webhook_dedup"

# 2. Revisar o arquivo gerado em alembic/versions/ — garantir que não há DROP TABLE acidental

# 3. Testar localmente
alembic upgrade head

# 4. Testar rollback
alembic downgrade -1

# 5. Só então aplicar em produção
```

### ⛔ 6.2 — Semáforo global em ambiente multi-worker

Conforme detalhado na seção 3.1: adicionar `asyncio.Semaphore` em ambiente multi-worker (Gunicorn + N workers) **não causa crash**, mas cria comportamento inesperado — o limite não funciona como esperado. Validar o modelo de deploy antes.

### ⛔ 6.3 — Loop de health check sem `try/except` externo

Se o `_zapi_health_loop` levantar uma exceção não capturada fora do `while True`, a corrotina termina silenciosamente — sem crash visível, mas o badge de status para de atualizar para sempre até o próximo deploy.

```python
# ✅ CERTO — proteção externa garante que o loop nunca morre
async def _zapi_health_loop():
    while True:
        try:
            result = await check_zapi_connectivity()
            _zapi_status_cache.update(result)
        except Exception as e:
            # captura TUDO — o loop nunca pode morrer
            logger.error(f"[ZAPI] Erro inesperado no health loop: {e}")
        await asyncio.sleep(300)
```

### ⛔ 6.4 — Validação de webhook sem fallback para payloads inesperados

Ao adicionar a validação do `Client-Token` no webhook, garantir que o handler retorna **HTTP 200 para payloads válidos mas de tipo desconhecido**. Se retornar erro para eventos que não reconhece, a Z-API vai tentar reenviar indefinidamente.

```python
# ✅ CERTO — evento desconhecido recebe 200 silencioso
event_type = payload.get("type") or payload.get("event")
if event_type not in HANDLED_EVENT_TYPES:
    logger.debug(f"[ZAPI] Evento ignorado: {event_type}")
    return {"status": "ignored"}  # 200 OK — não gera retry
```

### ⛔ 6.5 — Retry infinito acidental

No módulo de retry (seção 4.1), garantir que o loop tem limite máximo. Um loop sem limite pode travar uma coroutine por minutos e consumir conexões do pool de banco.

```python
# ✅ CERTO — máximo definido e explícito
MAX_RETRIES = 3
for attempt in range(MAX_RETRIES):
    ...

# ❌ ERRADO — sem limite
while not success:
    try:
        ...
    except:
        await asyncio.sleep(delay)
```

---

## 7. Checklist de entrega — como nos dar a devolutiva

Ao finalizar os commits, por favor, **responda com os itens abaixo** para que possamos fazer a revisão e dar a devolutiva:

### 7.1 — Arquivos modificados por item

| Item | Arquivo(s) alterado(s) | Linhas aproximadas |
|---|---|---|
| P0 — Idempotência | `services/whatsapp_client.py` | |
| P0 — Idempotência | `models.py` (nova tabela OutboxMessage) | |
| P0 — Segurança Webhook | `api/endpoints/whatsapp_webhook.py` | |
| P1 — Semáforo | `api/endpoints/whatsapp_webhook.py` | |
| P2 — Health check real | `services/dependency_check.py` | |
| P2 — Health loop | `main.py` (lifespan) | |
| P3 — Validação mídia | `services/whatsapp_client.py` | |
| Extra — Retry | `services/whatsapp_client.py` | |
| Extra — Rate limit | `services/` (arquivo de campanhas) | |

### 7.2 — Migration gerada

- Nome do arquivo de migration: `alembic/versions/___________`
- Tabelas criadas: `outbox_messages` / `received_webhooks`
- Testado rollback local: ✅ / ❌

### 7.3 — Variáveis de ambiente

Liste qualquer nova variável de ambiente adicionada ao `.env.example`:
```
# Ex:
ZAPI_WEBHOOK_SECRET=...
CAMPAIGN_DELAY_SECONDS=1.5
```

### 7.4 — Modelo de deploy confirmado

- [ ] Single-process (uvicorn simples) → semáforo funciona
- [ ] Multi-worker (gunicorn -w N) → anotar como dívida técnica, semáforo não resolve

### 7.5 — Endpoints novos ou modificados

Liste os endpoints novos ou com assinatura alterada para validarmos impacto no frontend:
```
GET  /api/integrations/zapi/health   → novo
POST /api/webhook/zapi               → agora exige Client-Token no header
```

### 7.6 — Itens deixados para próxima sprint

Se algum item desta revisão foi deliberadamente adiado, documente aqui com o motivo. Isso nos ajuda a não perder rastreabilidade:

| Item | Motivo do adiamento | Sprint prevista |
|---|---|---|
| | | |

---

> **Dúvidas ou pontos de decisão durante a implementação?**  
> Acione o canal interno antes de tomar uma decisão arquitetural que não estava prevista neste documento.  
> Alterações na estrutura do banco, no modelo de deploy ou nos endpoints públicos **sempre** merecem alinhamento antes do commit.

---

*Documento gerado em: março/2026 — Stevan · IA Interna SVN Renda Variável*
