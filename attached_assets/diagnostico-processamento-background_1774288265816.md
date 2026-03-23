# Diagnóstico: Processamento Persistente em Background

**Contexto:** Tela de Documentos — `agente-ia-rv-production.up.railway.app`  
**Problema central:** O processamento de documentos depende da sessão do browser. Ao recarregar a página, o estado é perdido e os jobs param.

---

## O que está acontecendo hoje

O fluxo atual funciona assim:

1. O usuário seleciona documentos e clica em "Processar"
2. O JavaScript do browser chama `POST /api/products/materials/{id}/resume-upload`
3. O backend abre um **SSE stream** (Server-Sent Events) e devolve progresso em tempo real
4. O frontend lê esse stream e atualiza a UI linha a linha
5. **O processamento vive dentro da conexão HTTP aberta entre browser e servidor**

Isso explica os dois sintomas que você observou:

- **"Processando 1/27" e os outros ficam parados:** O loop `for` no frontend processa os documentos *sequencialmente*, um de cada vez, aguardando o stream de cada um completar antes de chamar o próximo. Os outros 26 estão na fila dentro do JavaScript — não no servidor.
- **F5 mata tudo:** A conexão SSE é encerrada. O servidor para o que estava fazendo (ou termina o processamento mas não tem para onde devolver o resultado). O frontend perde o estado porque ele é mantido em variáveis em memória (`selectedIds`, estado das linhas).

---

## O que seria necessário para ter processamento persistente

Para que o processamento continue independentemente de quem está na tela, é preciso mover a responsabilidade de **orquestração e execução** do frontend para o backend. Isso envolve três componentes:

### 1. Fila de jobs no backend (o mais crítico)

Hoje o backend processa *na hora* quando recebe o POST. Para persistência, o POST deveria apenas **enfileirar** o job e devolver um ID. O processamento aconteceria em segundo plano, gerenciado pelo servidor.

**Opções de implementação:**

| Opção | Complexidade | Adequado para Railway |
|---|---|---|
| **Fila em banco de dados** (tabela `processing_jobs`) | Baixa | ✅ Sim |
| **Redis + worker** (Celery, ARQ, RQ) | Média | ✅ Sim (Railway tem Redis como add-on) |
| **Background tasks nativas do FastAPI** (`BackgroundTasks`) | Baixa | ⚠️ Limitado (não sobrevive a restart do processo) |

A opção mais segura para Railway sem adicionar infraestrutura nova é uma **tabela de jobs no banco de dados já existente**, combinada com um worker que roda em loop.

---

### 2. Persistência de status no banco de dados

Hoje o status ("Processando", "Concluído", "Erro") existe apenas na UI. O backend precisa gravar esses estados na base.

**O que verificar no código do backend:**

- A tabela de materiais (`materials`) já tem o campo `indexed` (booleano). Verificar se existe ou se é necessário adicionar campos como:
  - `processing_status` — enum: `pending`, `processing`, `done`, `error`
  - `processing_started_at` — timestamp
  - `processing_error` — texto do erro (parece já existir no frontend: `doc.processing_error`)
  - `processing_progress` — opcional, para exibir "Página X/Y"

- O frontend já consome `doc.processing_error` e `doc.indexed`, o que indica que o backend **já persiste ao menos o resultado final**. A questão é se o status intermediário também é salvo.

---

### 3. Polling no frontend (em vez de SSE preso à sessão)

Com o backend gerenciando os jobs, o frontend não precisa mais manter uma conexão aberta. Ele pode simplesmente consultar o status a cada N segundos.

**Mudança no frontend:**

```javascript
// Em vez de: abrir SSE e bloquear até completar
// Fazer: polling a cada 5s enquanto houver docs em processamento

function startPolling() {
    const interval = setInterval(async () => {
        await loadDocuments(); // recarrega da API
        const stillProcessing = allDocuments.some(d => d.processing_status === 'processing');
        if (!stillProcessing) clearInterval(interval);
    }, 5000);
}
```

Isso significa que qualquer usuário que abrir a tela vê o status atualizado, sem precisar ter disparado o processamento.

---

## Como diagnosticar o que já existe

Antes de construir qualquer coisa, responda estas perguntas olhando o código do backend:

### Passo 1 — Verificar o banco de dados

```sql
-- Rodar no banco de produção (Railway → PostgreSQL → Query)
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'materials'
ORDER BY ordinal_position;
```

**O que procurar:**
- Se existem colunas além de `indexed`: `status`, `processing_status`, `job_id`, etc.
- Se existe uma tabela separada de jobs: `SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';`

### Passo 2 — Verificar o endpoint de processamento

Localizar no backend o handler de `POST /api/products/materials/{id}/resume-upload` e verificar:

- O processamento roda **dentro do request** (síncrono/streaming) ou **dispara um worker** e retorna imediatamente?
- Existe alguma referência a `celery`, `arq`, `rq`, `dramatiq`, `asyncio.create_task` ou `BackgroundTasks`?
- O status do material é atualizado no banco durante o processamento, ou apenas ao final?

### Passo 3 — Verificar se há worker rodando

No Railway, verificar se existe mais de um serviço no projeto:
- Um serviço web (API + frontend)
- Um serviço worker separado

Se houver apenas um serviço, não há worker dedicado hoje.

### Passo 4 — Testar o comportamento real do backend

```bash
# Disparar o processamento de um documento
curl -X POST https://agente-ia-rv-production.up.railway.app/api/products/materials/{ID}/resume-upload \
  -H "Cookie: [seu cookie de sessão]" \
  --no-buffer

# Em outro terminal, consultar o status enquanto processa
# (se houver endpoint de status)
curl https://agente-ia-rv-production.up.railway.app/api/products/materials/{ID} \
  -H "Cookie: [seu cookie de sessão]"
```

Fechar o primeiro terminal no meio do processamento e verificar se o segundo ainda mostra progresso → indica que o backend processa de forma independente.

---

## Cenários possíveis e o que fazer em cada um

### Cenário A — Backend já persiste status, falta só o polling no frontend

**Sintoma:** A coluna `processing_status` existe no banco e é atualizada durante o processamento, mas o frontend não re-lê esses dados automaticamente.

**O que fazer:** Adicionar polling no `loadDocuments()` (mudança só no frontend, ~20 linhas).

**Esforço:** Baixo.

---

### Cenário B — Backend persiste apenas o resultado final (`indexed`), processa em background

**Sintoma:** O processamento continua após fechar o SSE, mas o frontend não sabe disso porque não há polling.

**O que fazer:** Adicionar campos intermediários de status no banco + polling no frontend.

**Esforço:** Médio (migração de banco + ajuste no backend + polling no frontend).

---

### Cenário C — Backend processa apenas durante a conexão SSE aberta (situação atual provável)

**Sintoma:** Fechar o SSE interrompe o processamento. Confirmado pelo comportamento observado.

**O que fazer:** Refatorar o endpoint para enfileirar o job e processar de forma assíncrona. Adicionar tabela ou campos de status. Adicionar polling no frontend.

**Esforço:** Alto (mudança de arquitetura no backend).

---

### Cenário D — Railway reinicia o processo durante o processamento

**Sintoma:** Mesmo com Cenário B implementado, jobs somem após deploy ou restart.

**O que fazer:** Adicionar Redis como add-on no Railway + usar ARQ ou RQ para gerenciar a fila com persistência entre restarts.

**Esforço:** Alto (nova infraestrutura).

---

## Recomendação de caminho mínimo

Se o objetivo é ter processamento persistente sem adicionar Redis ou reestruturar tudo:

1. **Adicionar campos no banco:** `processing_status`, `processing_started_at`, `processing_error` (verificar se já existem)
2. **No endpoint de processamento:** gravar `processing_status = 'processing'` ao iniciar e `'done'`/`'error'` ao terminar — independentemente de o SSE estar aberto
3. **No frontend:** substituir o SSE por polling a cada 5s enquanto houver documentos em processamento
4. **No endpoint POST:** retornar imediatamente com `202 Accepted` e rodar o processamento em `asyncio.create_task()` (FastAPI) — isso não sobrevive a restart, mas resolve o caso de F5

Isso cobre o cenário de uso principal (usuário dispara, sai da aba, volta e vê o status) sem exigir Redis ou worker dedicado.

---

## Próximos passos concretos

- [ ] Rodar a query SQL do Passo 1 e compartilhar o schema da tabela `materials`
- [ ] Localizar e compartilhar o código do handler `resume-upload` no backend
- [ ] Confirmar se há mais de um serviço rodando no Railway (web + worker)
- [ ] Testar o Passo 4 (fechar SSE no meio) para confirmar o Cenário C

Com essas informações em mãos, é possível definir com precisão o que precisa ser construído e o que já existe.
