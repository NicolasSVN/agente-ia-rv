# Plano de Implementação: Login com Microsoft SSO

> **Status**: Aguardando credenciais do time interno  
> **Data do Plano**: Fevereiro 2026  
> **Prioridade**: Pendente de dependência externa

---

## Visão Geral

O **SSO (Single Sign-On)** com Microsoft permite que os usuários façam login usando suas contas corporativas da Microsoft (@empresa.com.br). Isso utiliza o **Azure Active Directory (Azure AD)**, agora chamado **Microsoft Entra ID**.

---

## Fluxo de Autenticação

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FLUXO SSO MICROSOFT                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. Usuário clica "Entrar com Microsoft"                            │
│           │                                                          │
│           ▼                                                          │
│  2. Redireciona para login.microsoftonline.com                      │
│           │                                                          │
│           ▼                                                          │
│  3. Usuário digita e-mail e senha Microsoft                         │
│           │                                                          │
│           ▼                                                          │
│  4. Microsoft valida credenciais                                     │
│           │                                                          │
│           ▼                                                          │
│  5. Microsoft retorna código de autorização (callback)               │
│           │                                                          │
│           ▼                                                          │
│  6. Backend troca código por tokens (access_token + id_token)        │
│           │                                                          │
│           ▼                                                          │
│  7. Backend valida token e extrai dados do usuário                   │
│           │                                                          │
│           ▼                                                          │
│  8. Cria/atualiza usuário local + gera sessão JWT                   │
│           │                                                          │
│           ▼                                                          │
│  9. Usuário logado no sistema!                                       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## O Que Precisa Ser Feito no Azure Portal

### Passo 1: Acessar o Portal Azure

1. Acesse: https://portal.azure.com
2. Faça login com conta de administrador do Azure AD da empresa

### Passo 2: Registrar a Aplicação

1. Vá em **Azure Active Directory** (ou **Microsoft Entra ID**)
2. Clique em **Registros de aplicativo** → **Novo registro**
3. Preencha:
   - **Nome**: `Agente IA - RV` (ou nome desejado)
   - **Tipos de conta com suporte**: 
     - Escolha "Contas somente neste diretório organizacional" (Single Tenant)
   - **URI de Redirecionamento**: 
     - Tipo: **Web**
     - URL: `https://SEU_DOMINIO_REPLIT/auth/microsoft/callback`
4. Clique em **Registrar**

### Passo 3: Anotar as Credenciais

Após registrar, você verá:

| Campo | Onde Encontrar | Exemplo |
|-------|----------------|---------|
| **Client ID** | Página inicial do app → "ID do aplicativo (cliente)" | `12345678-abcd-1234-abcd-123456789abc` |
| **Tenant ID** | Página inicial do app → "ID do diretório (locatário)" | `87654321-dcba-4321-dcba-987654321cba` |

### Passo 4: Criar Client Secret

1. No menu lateral, clique em **Certificados e segredos**
2. Clique em **Novo segredo do cliente**
3. Descrição: `Agente IA RV - Produção`
4. Validade: **24 meses** (recomendado)
5. Clique **Adicionar**
6. **COPIE IMEDIATAMENTE** o valor do segredo (só aparece uma vez!)

| Campo | Valor |
|-------|-------|
| **Client Secret** | `abc123~XYZ.abcdefghijklmnop` |

### Passo 5: Configurar Permissões de API

1. Vá em **Permissões de API** → **Adicionar uma permissão**
2. Selecione **Microsoft Graph**
3. Escolha **Permissões delegadas**
4. Adicione:
   - `openid` ✓
   - `profile` ✓
   - `email` ✓
   - `User.Read` ✓
5. Clique em **Conceder consentimento do administrador** (botão azul)

### Passo 6: Configurar URI de Redirecionamento (Callback)

1. Vá em **Autenticação**
2. Em "URIs de redirecionamento", adicione:
   - `https://SEU_DOMINIO_REPLIT/auth/microsoft/callback`
3. Em "Configurações avançadas":
   - Marque: **Tokens de acesso** ✓
   - Marque: **Tokens de ID** ✓
4. Salve

---

## Variáveis Necessárias

Após completar os passos acima no Azure Portal, fornecer:

| Variável | Descrição | Formato |
|----------|-----------|---------|
| `MICROSOFT_CLIENT_ID` | ID da aplicação registrada | UUID (ex: `12345678-abcd-1234-abcd-123456789abc`) |
| `MICROSOFT_TENANT_ID` | ID do diretório/locatário | UUID (ex: `87654321-dcba-4321-dcba-987654321cba`) |
| `MICROSOFT_CLIENT_SECRET` | Segredo criado no passo 4 | String (ex: `abc123~XYZ.abcdefghijklmnop`) |

---

## Como Ficará no Sistema

### Tela de Login

```
┌────────────────────────────────────────┐
│                                        │
│           [Logo SVN]                   │
│                                        │
│     Bem-vindo ao Agente IA - RV        │
│                                        │
│  ┌──────────────────────────────────┐  │
│  │    🔐 Entrar com Microsoft       │  │
│  └──────────────────────────────────┘  │
│                                        │
│       ou                               │
│                                        │
│  ┌──────────────────────────────────┐  │
│  │  E-mail: ___________________     │  │
│  │  Senha:  ___________________     │  │
│  │                                  │  │
│  │        [ Entrar ]                │  │
│  └──────────────────────────────────┘  │
│                                        │
└────────────────────────────────────────┘
```

### Fluxo do Usuário

1. Usuário acessa a tela de login
2. Clica em **"Entrar com Microsoft"**
3. É redirecionado para a página da Microsoft
4. Digita e-mail corporativo e senha
5. Microsoft valida e redireciona de volta
6. Sistema cria/atualiza usuário automaticamente
7. Usuário é redirecionado para o Dashboard

---

## Implementação Técnica (Backend)

### Biblioteca Recomendada
```
fastapi-msal (para fluxo web com sessões)
```

### Endpoints que Serão Criados

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/auth/microsoft/login` | GET | Inicia o fluxo SSO, redireciona para Microsoft |
| `/auth/microsoft/callback` | GET | Recebe o retorno da Microsoft com o código |
| `/auth/microsoft/logout` | GET | Encerra sessão Microsoft |

### Dados Retornados pela Microsoft

Após autenticação, teremos acesso a:

```json
{
  "oid": "user-unique-id",
  "name": "João Silva",
  "preferred_username": "joao.silva@empresa.com.br",
  "email": "joao.silva@empresa.com.br",
  "given_name": "João",
  "family_name": "Silva"
}
```

### Mapeamento de Usuário

O sistema irá:
1. Verificar se existe usuário com o e-mail Microsoft
2. Se existir: atualiza dados e faz login
3. Se não existir: cria novo usuário com role `broker` (padrão)

---

## Checklist de Configuração

### No Azure Portal (Time Interno)
- [ ] Acessar Azure Portal com conta admin
- [ ] Criar registro de aplicação
- [ ] Copiar Client ID
- [ ] Copiar Tenant ID
- [ ] Criar Client Secret e copiar valor
- [ ] Configurar permissões (openid, profile, email, User.Read)
- [ ] Conceder consentimento do administrador
- [ ] Adicionar URI de callback correto
- [ ] Habilitar tokens de acesso e ID

### No Replit (Após Receber Variáveis)
- [ ] Instalar dependências (fastapi-msal, python-multipart)
- [ ] Criar endpoints de autenticação Microsoft
- [ ] Adicionar botão "Entrar com Microsoft" na tela de login
- [ ] Implementar lógica de criação/atualização de usuário
- [ ] Testar fluxo completo

---

## Segurança

- **Client Secret**: Nunca expor em código ou logs
- **HTTPS obrigatório**: Callback só funciona com HTTPS
- **Validação de Token**: Verificamos assinatura e claims
- **Single Tenant**: Apenas usuários do seu diretório podem logar

---

## Próximos Passos

1. **Time Interno**: Complete o checklist "No Azure Portal"
2. **Time Interno**: Fornecer os 3 valores (Client ID, Tenant ID, Client Secret)
3. **Agente**: Adicionar como Secrets no Replit
4. **Agente**: Implementar toda a integração
5. **Todos**: Testar juntos

---

## Dependências Python a Instalar

```bash
pip install fastapi-msal python-multipart
```

Ou adicionar ao requirements.txt:
```
fastapi-msal
python-multipart
```

---

## Código de Exemplo (Referência)

```python
from fastapi import FastAPI, Depends
from starlette.middleware.sessions import SessionMiddleware
from fastapi_msal import MSALAuthorization, UserInfo, MSALClientConfig

client_config = MSALClientConfig()
client_config.client_id = os.getenv("MICROSOFT_CLIENT_ID")
client_config.client_credential = os.getenv("MICROSOFT_CLIENT_SECRET")
client_config.tenant = os.getenv("MICROSOFT_TENANT_ID")

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="YOUR_SECRET_KEY")

msal_auth = MSALAuthorization(client_config=client_config)
app.include_router(msal_auth.router)

@app.get("/users/me", response_model=UserInfo)
async def read_users_me(current_user: UserInfo = Depends(msal_auth.scheme)):
    return current_user
```

---

## Endpoints Microsoft (Referência)

```python
TENANT_ID = os.getenv("MICROSOFT_TENANT_ID")

# Autorização
AUTH_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize"

# Troca de token
TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

# Chaves públicas para validação
JWKS_URL = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"

# Configuração OpenID
OPENID_CONFIG = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0/.well-known/openid-configuration"
```
