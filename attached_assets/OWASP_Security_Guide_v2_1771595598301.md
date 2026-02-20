# Guia de Segurança — Stevan
## OWASP Top 10:2025 | Auditoria Real + Plano de Ação + Cenários de Teste

---

> **Contexto da aplicação:** Python (FastAPI/Flask) · SQLAlchemy ORM · Jinja2 · bcrypt · JWT próprio · Integrações externas: OpenAI, Z-API, Tavily, FundsExplorer · Autenticação: JWT interno + SSO Microsoft (verificar integração).
>
> **Como usar este documento:** A Fase 1 contém o diagnóstico consolidado com achados reais do Replit + recomendações de correção. A Fase 2 contém cenários de teste personalizados para esta aplicação. A Fase 3 é o checklist de pré-lançamento.

---

## STATUS GERAL DA AUDITORIA

| # | Categoria | Status | Risco | Resumo do Achado Real |
|---|-----------|--------|-------|-----------------------|
| A01 | Broken Access Control | 🟡 Parcial | Alto | JWT e roles existem, mas sem verificação global — endpoints sem check ficam abertos. Risco de IDOR presente. |
| A02 | Security Misconfiguration | 🔴 Crítico | Crítico | Zero security headers. SECRET_KEY hardcoded com valor padrão. CORS possivelmente permissivo. |
| A03 | Supply Chain Failures | 🔴 Ausente | Médio | Sem pip-audit. requirements.txt sem lockfile. |
| A04 | Cryptographic Failures | 🟡 Parcial | Alto | bcrypt correto. JWT expira em 24h (longo demais). Sem validação de issuer/audience. |
| A05 | Injection | 🟢 Bom | Baixo | SQLAlchemy ORM e Jinja2 auto-escape protegem. Risco residual: prompt injection no OpenAI. |
| A06 | Insecure Design | 🔴 Ausente | Alto | Sem rate limiting no login. Sem lockout. Sem proteção contra exaustão das API keys externas. |
| A07 | Auth Failures | 🟡 Parcial | Alto | JWT + bcrypt funcionando. Sem MFA, sem lockout, sem proteção contra credential stuffing. |
| A08 | Data Integrity | 🟡 Parcial | Médio | Uploads de PDF sem verificação de integridade. |
| A09 | Logging & Monitoring | 🔴 Ausente | Alto | Sem trilha de auditoria. Sem log de logins falhos. Logs espalhados sem estrutura. |
| A10 | Exceptional Conditions | 🟡 Parcial | Médio | try/except genéricos podem vazar stack traces. Sem handler global. Risco de fail open. |

---

# FASE 1 — DIAGNÓSTICO E PLANO DE CORREÇÃO

---

## ⚠️ NOTA CRÍTICA: SSO Microsoft vs. JWT Interno

Antes de qualquer correção técnica, é essencial entender como o SSO da Microsoft se relaciona com o sistema JWT interno da aplicação. O relatório do Replit mostra que existe um sistema de autenticação próprio (JWT + bcrypt) rodando na aplicação. O SSO da Microsoft pode estar sendo usado como camada adicional, mas se os dois sistemas coexistem de forma independente, qualquer um deles se tornando vulnerável compromete toda a segurança.

**A pergunta que precisa ser respondida antes de continuar:** Quando um usuário faz login via SSO da Microsoft, a aplicação gera um JWT próprio a partir do token da Microsoft — ou os dois sistemas são caminhos paralelos de acesso? Se for paralelo, isso cria uma superfície de ataque dupla.

---

## A01 — BROKEN ACCESS CONTROL 🟡 Parcial

**O que foi encontrado:** JWT com roles está implementado e os endpoints usam `get_current_user`, o que é um bom começo. Porém, a ausência de uma verificação global significa que qualquer endpoint criado sem o decorator correto fica aberto silenciosamente. Além disso, há risco de IDOR — situações onde um usuário pode acessar um recurso de outro usuário apenas alterando o ID na URL ou no body da requisição.

As chamadas externas para OpenAI, Z-API, Tavily e FundsExplorer também foram sinalizadas como sem proteção contra SSRF (Server-Side Request Forgery), que é quando um atacante induz a aplicação a fazer chamadas HTTP para destinos não autorizados usando essas integrações como vetor.

**Prompt de correção para o Replit AI:**

```
Em relação ao A01 (Broken Access Control), preciso de três correções específicas:

1. VERIFICAÇÃO GLOBAL DE AUTENTICAÇÃO: Implemente um middleware ou dependency global no FastAPI
   que exija autenticação por padrão em todas as rotas, com opt-out explícito apenas para rotas
   públicas (ex: login, health check). O objetivo é inverter a lógica atual: em vez de "rotas
   protegidas quando o developer lembra de adicionar o decorator", passa a ser "todas as rotas
   protegidas, exceto as explicitamente marcadas como públicas".

2. PROTEÇÃO CONTRA IDOR: Para cada endpoint que receba um ID de recurso (ex: document_id,
   user_id, report_id), adicione uma query que valide se o recurso pertence ao usuário autenticado
   antes de retornar ou modificar dados. Exemplo: ao buscar /api/documents/{doc_id}, não basta
   encontrar o documento — é preciso verificar que document.owner_id == current_user.id.

3. ALLOWLIST PARA CHAMADAS EXTERNAS (SSRF): Nas integrações com OpenAI, Z-API, Tavily e
   FundsExplorer, crie uma allowlist de domínios permitidos. Qualquer URL construída dinamicamente
   com input do usuário deve ser validada contra essa lista antes da chamada HTTP ser executada.
   Nunca deixe o usuário controlar diretamente a URL de destino de uma chamada externa.
```

---

## A02 — SECURITY MISCONFIGURATION 🔴 CRÍTICO

**O que foi encontrado:** Este é o item mais urgente. A aplicação não tem nenhum security header configurado — CSP, HSTS, X-Frame-Options e X-Content-Type-Options estão ausentes. Mais grave ainda: a `SECRET_KEY` usada para assinar os JWTs tem o valor padrão `"dev-secret-key-change-in-production"` hardcoded no código. Isso significa que qualquer pessoa que leia o repositório (ou que simplesmente conheça esse padrão comum) pode forjar tokens JWT válidos e se passar por qualquer usuário da aplicação, incluindo administradores. Esta vulnerabilidade, sozinha, invalida toda a proteção do sistema de autenticação.

**Prompt de correção para o Replit AI:**

```
Em relação ao A02 (Security Misconfiguration), preciso de três correções imediatas:

1. SECURITY HEADERS: Adicione um middleware global que injete os seguintes headers em todas
   as respostas HTTP:
   - Content-Security-Policy: default-src 'self'; script-src 'self'; object-src 'none'
   - X-Frame-Options: DENY
   - X-Content-Type-Options: nosniff
   - Strict-Transport-Security: max-age=31536000; includeSubDomains (apenas em produção)
   - Referrer-Policy: strict-origin-when-cross-origin
   - Permissions-Policy: geolocation=(), microphone=(), camera=()

2. SECRET_KEY SEGURA: Remova qualquer valor padrão da SECRET_KEY. O código deve falhar
   explicitamente na inicialização se a variável de ambiente SECRET_KEY não estiver definida.
   Use algo como:
   SECRET_KEY = os.environ.get("SECRET_KEY")
   if not SECRET_KEY:
       raise RuntimeError("SECRET_KEY environment variable is required and not set.")
   Gere uma chave segura com: python -c "import secrets; print(secrets.token_hex(64))"
   e armazene no Secrets do Replit.

3. CORS RESTRITIVO: Configure o CORS para aceitar apenas as origens explicitamente listadas
   (o domínio do frontend em produção). Nunca use allow_origins=["*"] em produção.
   Em desenvolvimento, use uma variável de ambiente ALLOWED_ORIGINS separada.
```

---

## A03 — SUPPLY CHAIN FAILURES 🔴 Ausente

**O que foi encontrado:** Não há auditoria de dependências configurada e o requirements.txt não tem um lockfile equivalente (como poetry.lock ou pip freeze com hashes), o que significa que não há garantia de que os pacotes instalados em produção são os mesmos que foram testados em desenvolvimento, e que vulnerabilidades conhecidas em dependências podem ter passado despercebidas.

**Prompt de correção para o Replit AI:**

```
Em relação ao A03 (Supply Chain), execute as seguintes ações:

1. Execute `pip-audit` no projeto (instale com `pip install pip-audit` se necessário) e liste
   todas as vulnerabilidades encontradas. Para cada vulnerabilidade HIGH ou CRITICAL, atualize
   o pacote imediatamente.

2. Gere um requirements.txt com versões fixas e hashes:
   pip freeze > requirements.txt
   Isso garante que instalações futuras usem exatamente os mesmos pacotes.

3. Identifique e remova qualquer dependência instalada que não esteja sendo usada no código.

4. Documente no README o comando para re-executar a auditoria periodicamente antes de deploys.
```

---

## A04 — CRYPTOGRAPHIC FAILURES 🟡 Parcial

**O que foi encontrado:** O uso de bcrypt para senhas é correto — esse é o caminho certo. Os problemas estão no JWT: a expiração de 24 horas é longa demais para um token de acesso (o padrão da indústria é 15 minutos a 1 hora, com refresh tokens separados), e não há validação de `issuer` e `audience`, o que significa que um token gerado por outra aplicação que use a mesma chave poderia ser aceito.

**Prompt de correção para o Replit AI:**

```
Em relação ao A04 (Cryptographic Failures), faça as seguintes correções no sistema JWT:

1. Reduza o tempo de expiração do access token para 60 minutos (no máximo).

2. Implemente um sistema de refresh token separado com expiração de 7 dias. O refresh token
   deve ser armazenado de forma segura (httpOnly cookie ou banco de dados com hash).

3. Adicione os claims `iss` (issuer) e `aud` (audience) na geração do JWT e valide-os na
   decodificação. Exemplo:
   - iss: "stevan-api"
   - aud: "stevan-frontend"
   Isso impede que tokens gerados por outros sistemas sejam aceitos.

4. Se o SSO da Microsoft estiver em uso, valide também os claims `iss` e `aud` do token
   Microsoft (o issuer deve ser a URL do tenant Azure AD da organização).
```

---

## A05 — INJECTION 🟢 Bom

**O que foi encontrado:** Este é o ponto mais sólido da aplicação. O SQLAlchemy ORM protege naturalmente contra SQL Injection ao parametrizar todas as queries, e o Jinja2 com auto-escape ativado previne XSS nos templates. O único risco residual identificado é **prompt injection** nas chamadas ao OpenAI — uma categoria relativamente nova de vulnerabilidade onde um usuário mal-intencionado insere instruções no conteúdo enviado ao modelo para tentar manipular seu comportamento.

**Prompt de correção para o Replit AI:**

```
Em relação ao A05 (Injection), o único item a endereçar é o risco de prompt injection no OpenAI:

1. Identifique todos os pontos onde conteúdo gerado pelo usuário é incluído no prompt enviado
   ao OpenAI (ex: conteúdo de documentos, campos de formulário, mensagens).

2. Para cada ponto, separe claramente o conteúdo do usuário das instruções do sistema usando
   a estrutura de mensagens correta da API (system message separado do user message). Nunca
   concatene instruções do sistema com input do usuário em uma única string.

3. Adicione uma nota no sistema de validação de input: se o conteúdo enviado ao modelo parecer
   conter instruções para ignorar regras anteriores, registre no log e opcionalmente rejeite.
```

---

## A06 — INSECURE DESIGN 🔴 Ausente

**O que foi encontrado:** A ausência de rate limiting no endpoint de login é uma vulnerabilidade séria — sem ela, um atacante pode fazer centenas de tentativas de senha por segundo sem nenhuma resistência. O problema se estende também às API keys externas (OpenAI, Tavily): sem limites de uso, um usuário pode esgotar a cota da API key em minutos, causando negação de serviço para todos os demais usuários.

**Prompt de correção para o Replit AI:**

```
Em relação ao A06 (Insecure Design), implemente rate limiting em múltiplas camadas:

1. RATE LIMITING NO LOGIN: Use a biblioteca `slowapi` (para FastAPI) ou `flask-limiter`
   (para Flask) para limitar tentativas de login a 5 por minuto por IP. Após 10 tentativas
   falhas consecutivas do mesmo IP, bloqueie por 15 minutos.
   Exemplo com slowapi:
   @limiter.limit("5/minute")
   async def login(request: Request, ...):

2. LOCKOUT POR USUÁRIO: Após 5 tentativas falhas para o mesmo username (independente do IP),
   bloqueie a conta por 10 minutos e registre no log. Armazene o contador de falhas no banco
   ou em cache.

3. PROTEÇÃO DAS API KEYS EXTERNAS: Para OpenAI e Tavily, implemente um rate limit por usuário
   autenticado (ex: máximo de 20 chamadas por hora por usuário). Isso impede que um usuário
   esgote a cota da organização inteira.

4. Retorne sempre HTTP 429 (Too Many Requests) com um header Retry-After indicando quando
   o usuário pode tentar novamente.
```

---

## A07 — AUTH FAILURES 🟡 Parcial

**O que foi encontrado:** A base está correta (JWT + bcrypt), mas faltam camadas de proteção que se tornaram padrão de mercado. A ausência de MFA é notável especialmente considerando que o SSO da Microsoft já pode fornecer isso nativamente. O que precisa ser verificado é se o MFA do Azure AD está sendo exigido pela política do tenant — se estiver, isso já resolve essa lacuna para os usuários que fazem login pelo SSO.

**Prompt de correção para o Replit AI:**

```
Em relação ao A07 (Auth Failures):

1. LOGOUT COMPLETO: Implemente uma blacklist de tokens JWT inválidos (usando Redis ou uma
   tabela no banco com os JTI — JWT ID — dos tokens revogados). Quando o usuário fizer logout,
   o token atual deve ser adicionado à blacklist e rejeitado em requisições subsequentes, mesmo
   que ainda não tenha expirado.

2. SINGLE LOGOUT COM SSO: Se o usuário fizer logout pelo SSO da Microsoft, a sessão local da
   aplicação também deve ser encerrada. Consulte a documentação do MSAL para implementar o
   fluxo de Single Logout.

3. VERIFICAÇÃO DO TOKEN MICROSOFT: Se a aplicação aceita tokens do SSO da Microsoft, use a
   biblioteca `msal` ou `python-jose` para validar a assinatura, o issuer (URL do tenant Azure),
   e o audience (o client_id da aplicação registrada no Azure AD).

4. PROTEÇÃO CONTRA CREDENTIAL STUFFING: Além do rate limiting por IP, implemente detecção
   básica de anomalia: se o mesmo usuário tenta login de IPs muito diferentes em curto espaço
   de tempo, registre como suspeito e considere exigir re-verificação.
```

---

## A08 — DATA INTEGRITY FAILURES 🟡 Parcial

**O que foi encontrado:** Os uploads de PDF não têm verificação de integridade, o que abre dois vetores: arquivos corrompidos sendo processados silenciosamente, e potencialmente arquivos maliciosos sendo aceitos (ex: um PDF com payload embutido). Para uma aplicação que processa documentos financeiros, isso é especialmente relevante.

**Prompt de correção para o Replit AI:**

```
Em relação ao A08 (Data Integrity), corrija o processo de upload de PDF:

1. Valide o tipo MIME do arquivo no servidor (não confie no Content-Type do request).
   Use a biblioteca `python-magic` para verificar a assinatura do arquivo:
   import magic
   mime = magic.from_buffer(file_content, mime=True)
   if mime != "application/pdf":
       raise ValueError("Tipo de arquivo não permitido")

2. Defina um tamanho máximo de arquivo e rejeite uploads que excedam o limite.

3. Gere e armazene um hash SHA-256 de cada arquivo no momento do upload. Isso permite
   verificar integridade futura e detectar arquivos modificados ou corrompidos.
   import hashlib
   file_hash = hashlib.sha256(file_content).hexdigest()

4. Considere executar o PDF em um ambiente isolado (sandboxed) se ele for processado
   ou renderizado — PDFs podem conter JavaScript embutido.
```

---

## A09 — LOGGING & MONITORING 🔴 Ausente

**O que foi encontrado:** Este é o segundo item mais crítico para a operação em produção. Sem trilha de auditoria, sem log de tentativas de login falhas e sem estrutura centralizada, a aplicação não tem nenhuma capacidade de detectar que está sendo atacada, investigar incidentes após o fato, ou demonstrar conformidade. Em uma aplicação que lida com dados financeiros, a ausência de logging estruturado pode ser também um problema regulatório.

**Prompt de correção para o Replit AI:**

```
Em relação ao A09 (Logging & Monitoring), implemente logging estruturado em três camadas:

1. CONFIGURAÇÃO BASE: Configure o módulo `logging` do Python com formato estruturado JSON:
   import logging, json
   logging.basicConfig(
       level=logging.INFO,
       format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
              '"event": "%(message)s", "module": "%(module)s"}'
   )
   Isso permite que logs sejam facilmente indexados e pesquisados.

2. EVENTOS DE SEGURANÇA OBRIGATÓRIOS — registre SEMPRE os seguintes eventos:
   - Login com sucesso: user_id, ip, timestamp, método (jwt/sso)
   - Login com falha: username tentado (nunca a senha), ip, timestamp, motivo
   - Logout: user_id, timestamp
   - Acesso negado (403): user_id, endpoint tentado, ip
   - Token inválido/expirado: ip, endpoint, timestamp
   - Ação administrativa: user_id, ação realizada, dados afetados
   - Upload de arquivo: user_id, nome do arquivo, hash, timestamp

3. O QUE NUNCA DEVE APARECER EM LOGS:
   - Senhas (nem cifradas)
   - Tokens JWT completos ou cookies de sessão
   - SECRET_KEY ou qualquer chave de API
   - Dados pessoais sensíveis completos (mascare CPF, emails com **)
   - Stack traces completos (esses vão para arquivo de log separado, nunca para o console)

4. SEPARAÇÃO DE LOGS: Crie dois destinos de log:
   - security.log: apenas eventos de segurança (estruturado JSON)
   - error.log: exceções e stack traces (apenas para diagnóstico interno)
```

---

## A10 — EXCEPTIONAL CONDITIONS 🟡 Parcial

**O que foi encontrado:** Existem vários blocos `try/except` genéricos que podem vazar stack traces para o usuário, e não há um handler global que padronize as respostas de erro. O risco de "fail open" ocorre quando um erro na verificação de permissão resulta em acesso liberado em vez de acesso negado — um comportamento silencioso que pode passar despercebido.

**Prompt de correção para o Replit AI:**

```
Em relação ao A10 (Exceptional Conditions):

1. HANDLER GLOBAL DE ERROS: Implemente um exception handler global que capture todas as
   exceções não tratadas e retorne sempre uma resposta genérica:
   @app.exception_handler(Exception)
   async def global_exception_handler(request, exc):
       logger.error(f"Unhandled exception: {exc}", exc_info=True)  # detalhe vai pro log
       return JSONResponse(
           status_code=500,
           content={"error": "Ocorreu um erro interno. Por favor, tente novamente."}
       )

2. FAIL CLOSED: Revise todos os blocos try/except que envolvem validação de autenticação
   ou autorização. Qualquer exceção nesses blocos deve resultar em acesso NEGADO (403 ou 401),
   nunca em acesso liberado. Padrão seguro:
   try:
       user = validate_token(token)
   except Exception:
       raise HTTPException(status_code=401, detail="Não autorizado")  # sempre nega

3. ERROS DO BANCO DE DADOS: Envolva todas as operações de banco em handlers que capturem
   SQLAlchemyError e retornem mensagem genérica, nunca o texto da exceção original (que pode
   revelar nomes de tabelas, colunas ou estrutura do schema).

4. Revise todos os except genéricos (except Exception: pass) — silenciar exceções é perigoso.
   Todo except deve pelo menos registrar o erro no log.
```

---

# FASE 2 — CENÁRIOS DE TESTE PERSONALIZADOS

> Estes cenários foram adaptados para os achados reais desta aplicação. O objetivo é que todos os ataques **falhem** após as correções da Fase 1 serem implementadas.

---

## TESTE 1 — Forge de Token JWT (A02/A04) · Risco: CRÍTICO

**O que testa:** Se a SECRET_KEY insegura permite forjar tokens de administrador.

**Como executar:** Antes de corrigir o A02, tente gerar um JWT manualmente usando a chave padrão `"dev-secret-key-change-in-production"` com um payload de admin. Use o site jwt.io ou a biblioteca PyJWT localmente:

```python
import jwt
token = jwt.encode(
    {"sub": "qualquer_email@teste.com", "role": "admin", "exp": 9999999999},
    "dev-secret-key-change-in-production",
    algorithm="HS256"
)
# Tente usar esse token no header Authorization: Bearer <token>
```

**Resultado esperado após correção:** `401 Unauthorized`. Com a SECRET_KEY trocada por um valor forte e aleatório, tokens gerados externamente são inválidos.

---

## TESTE 2 — IDOR em Documentos/Recursos (A01)

**O que testa:** Se um usuário consegue acessar documentos de outro usuário por ID.

**Como executar:**
1. Faça login com o Usuário A e crie ou acesse um documento. Anote o ID (ex: `/api/documents/42`).
2. Em outra sessão (ou usando o token do Usuário B), tente acessar `GET /api/documents/42`.
3. Tente também `GET /api/documents/1`, `GET /api/documents/2` para varredura.

**Resultado esperado:** `403 Forbidden` ou `404 Not Found` para todos os recursos que não pertencem ao usuário autenticado.

---

## TESTE 3 — Rate Limiting no Login (A06)

**O que testa:** Se a proteção contra força bruta está funcionando.

**Como executar:** Use um script simples ou o Postman com repetição para enviar 15 requisições de login em sequência com senha incorreta:

```bash
for i in {1..15}; do
  curl -X POST https://seu-app.replit.app/api/login \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@teste.com","password":"senha_errada"}' \
    -w " → HTTP %{http_code}\n" -s -o /dev/null
done
```

**Resultado esperado:** As primeiras 5 retornam `401`. A partir da 6ª, devem retornar `429 Too Many Requests`.

---

## TESTE 4 — Security Headers (A02)

**O que testa:** Se os headers de proteção estão presentes em todas as respostas.

**Como executar:** Acesse o site [securityheaders.com](https://securityheaders.com) e insira a URL da aplicação. Ou use curl:

```bash
curl -I https://seu-app.replit.app/
```

**Resultado esperado:** Nota A ou B no securityheaders.com. Os headers `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options` e `Strict-Transport-Security` devem estar presentes.

---

## TESTE 5 — Stack Trace em Resposta de Erro (A10)

**O que testa:** Se erros internos expõem detalhes da implementação.

**Como executar:** Envie requisições malformadas para endpoints da API:

```bash
# JSON inválido
curl -X POST https://seu-app.replit.app/api/login \
  -H "Content-Type: application/json" \
  -d '{"email": INVALIDO}'

# Tipo errado
curl -X GET https://seu-app.replit.app/api/documents/nao_e_um_numero
```

**Resultado esperado:** Resposta JSON com mensagem genérica (`"Ocorreu um erro interno"`), código 400 ou 500. Nenhum trecho de código Python, nome de arquivo ou traceback deve aparecer.

---

## TESTE 6 — Logout e Reutilização de Token (A07)

**O que testa:** Se o token JWT é invalidado após o logout.

**Como executar:**
1. Faça login e copie o token JWT do header `Authorization` de qualquer requisição (visível no DevTools > Network).
2. Faça logout normalmente pela interface.
3. Com o token copiado, tente uma requisição autenticada via curl:

```bash
curl https://seu-app.replit.app/api/me \
  -H "Authorization: Bearer SEU_TOKEN_COPIADO_AQUI"
```

**Resultado esperado:** `401 Unauthorized`. O token não deve funcionar após o logout, mesmo que ainda não tenha expirado.

---

## TESTE 7 — Upload de PDF Malformado (A08)

**O que testa:** Se o backend valida realmente o tipo do arquivo ou confia no frontend.

**Como executar:**
1. Renomeie um arquivo de imagem PNG para `documento.pdf` e tente fazer upload.
2. Tente também enviar um arquivo de texto com extensão .pdf.
3. Tente enviar um arquivo muito grande (acima do limite esperado).

**Resultado esperado:** A aplicação deve rejeitar os arquivos 1 e 2 com erro de validação de tipo MIME, e rejeitar o arquivo 3 com erro de tamanho.

---

## TESTE 8 — Verificação de Dependências (A03)

**O que testa:** Se há vulnerabilidades conhecidas nas dependências instaladas.

**Como executar:** No terminal do Replit:

```bash
pip install pip-audit
pip-audit
```

**Resultado esperado:** Zero vulnerabilidades com severidade HIGH ou CRITICAL. Se houver, corrigir antes do lançamento.

---

## TESTE 9 — Rotas Sem Autenticação (A01/A07)

**O que testa:** Se alguma rota que deveria ser protegida responde sem token.

**Como executar:** Faça uma lista de todos os endpoints da aplicação (você pode encontrá-los no código ou acessando `/docs` se o FastAPI estiver configurado). Para cada endpoint que deveria exigir autenticação, tente acessá-lo sem o header Authorization:

```bash
curl https://seu-app.replit.app/api/endpoint-protegido
# sem header de autenticação
```

**Resultado esperado:** `401 Unauthorized` em todos os endpoints protegidos.

---

## TESTE 10 — Logs de Segurança (A09)

**O que testa:** Se eventos críticos estão sendo registrados sem expor dados sensíveis.

**Como executar:**
1. Faça um login com sucesso e um login com falha.
2. Faça logout.
3. Acesse os logs do Replit (Console ou arquivo de log configurado).
4. Verifique se esses eventos aparecem com timestamp, user e IP.
5. Busque nos logs pelos termos: `Bearer`, `password`, `secret`, `token` como valores (não como chaves de log).

**Resultado esperado:** Os três eventos estão logados com estrutura JSON. Nenhum valor de token, senha ou chave aparece nos logs.

---

# FASE 3 — CHECKLIST DE PRÉ-LANÇAMENTO

| # | Item | Prioridade | Status |
|---|------|------------|--------|
| 1 | SECRET_KEY substituída por valor forte (64+ chars hex) e em variável de ambiente | 🔴 Crítico | ⬜ |
| 2 | Security headers presentes em todas as respostas | 🔴 Crítico | ⬜ |
| 3 | CORS configurado com origens explícitas (sem `*`) | 🔴 Crítico | ⬜ |
| 4 | Rate limiting no login (5 req/min por IP, lockout após 10 falhas) | 🔴 Crítico | ⬜ |
| 5 | Verificação de IDOR em todos os endpoints com ID de recurso | 🔴 Alto | ⬜ |
| 6 | Middleware de autenticação global (fail closed por padrão) | 🔴 Alto | ⬜ |
| 7 | Handler global de erros (sem stack traces para o usuário) | 🔴 Alto | ⬜ |
| 8 | Logging estruturado de eventos de segurança | 🔴 Alto | ⬜ |
| 9 | JWT expira em ≤60 minutos (com refresh token separado) | 🟡 Alto | ⬜ |
| 10 | Validação de issuer/audience no JWT | 🟡 Alto | ⬜ |
| 11 | SSO Microsoft integrado ao sistema JWT (Single Logout) | 🟡 Alto | ⬜ |
| 12 | Upload de PDF valida MIME no servidor (não apenas extensão) | 🟡 Médio | ⬜ |
| 13 | pip-audit sem vulnerabilidades HIGH/CRITICAL | 🟡 Médio | ⬜ |
| 14 | Allowlist de domínios nas chamadas externas (SSRF) | 🟡 Médio | ⬜ |
| 15 | Rate limit nas chamadas às API keys externas (por usuário) | 🟡 Médio | ⬜ |
| 16 | Todos os 10 cenários de teste executados e aprovados | ✅ Gate | ⬜ |

---

**Ordem recomendada de execução:** Itens 1→4 são o "cinto de segurança mínimo" — a aplicação não deveria ir a produção sem eles. Os itens 5→8 devem ser feitos na mesma sprint. Os itens 9→15 podem ser tratados na primeira semana pós-lançamento se necessário, mas idealmente antes.

---

*Documento baseado no OWASP Top 10:2025, auditoria do Replit AI e análise contextual do stack da aplicação Stevan.*
*Referências: owasp.org/Top10 · owasp.org/ASVS · docs.microsoft.com/azure/active-directory*
