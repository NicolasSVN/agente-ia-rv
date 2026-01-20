# Assessor IA - Agente de IA para Assessores Financeiros

## Visão Geral

Aplicação FastAPI completa para um agente de IA de assessores financeiros. O sistema comunica-se via WhatsApp usando WAHA API, realiza busca semântica em uma base de conhecimento do Notion usando ChromaDB e embeddings OpenAI, e inclui um painel administrativo com sistema de tickets Kanban e gerenciamento de usuários com autenticação JWT.

## Estrutura do Projeto

```
├── main.py                 # Ponto de entrada da aplicação
├── indexer.py              # Script para indexar conteúdo do Notion
├── core/
│   ├── config.py           # Configurações e variáveis de ambiente
│   └── security.py         # Funções de segurança (JWT, hash)
├── database/
│   ├── database.py         # Configuração SQLAlchemy
│   ├── models.py           # Modelos User e Ticket
│   └── crud.py             # Operações CRUD
├── services/
│   ├── openai_agent.py     # Agente de IA com OpenAI
│   ├── vector_store.py     # ChromaDB para busca semântica
│   └── whatsapp_service.py # Integração WAHA API
├── api/endpoints/
│   ├── auth.py             # Autenticação e login
│   ├── users.py            # Gerenciamento de usuários
│   ├── tickets.py          # Sistema de tickets Kanban
│   └── whatsapp_webhook.py # Webhook para mensagens WhatsApp
└── frontend/
    ├── templates/          # Templates HTML (Jinja2)
    └── static/             # CSS e assets
```

## Configuração de Secrets

### Obrigatórios para Produção
- `OPENAI_API_KEY` - Chave da API OpenAI para embeddings e chat
- `NOTION_API_KEY` - Chave da API Notion para indexar documentos
- `WAHA_API_URL` - URL da instância WAHA para WhatsApp

### Opcionais
- `DATABASE_URL` - URL PostgreSQL (usa SQLite local se não definido)
- `SESSION_SECRET` - Chave secreta para JWT
- `ADMIN_USERNAME` - Nome de usuário admin (padrão: admin)
- `ADMIN_PASSWORD` - Senha do admin (padrão: admin123 - ALTERAR EM PRODUÇÃO!)
- `ADMIN_EMAIL` - Email do admin

## Rotas Principais

### API
- `POST /api/auth/login` - Autenticação
- `GET /api/users/` - Listar usuários (admin)
- `GET /api/tickets/` - Listar tickets
- `POST /webhook/whatsapp` - Webhook WAHA
- `GET /api/integrations/` - Listar integrações (admin)
- `GET /api/integrations/{id}/status` - Testar conexão (admin)

### Frontend
- `/login` - Página de login
- `/kanban` - Quadro Kanban (admin/broker)
- `/admin` - Gerenciamento de usuários (admin)
- `/integrations` - Gerenciamento de integrações (admin)

## Roles de Usuário
- `admin` - Acesso total
- `broker` - Acesso ao Kanban
- `client` - Apenas via WhatsApp

## Execução

A aplicação roda em `http://0.0.0.0:5000`.

Para indexar documentos do Notion:
```bash
python indexer.py
```

## Gerenciamento de Integrações

A página `/integrations` (apenas admin) permite:
- Visualizar status das integrações configuradas (OpenAI, Notion, WAHA)
- Ver quais variáveis de ambiente estão configuradas
- Testar conexões com serviços externos
- Ativar/desativar integrações

**Importante:** As chaves de API devem ser configuradas via Secrets do Replit (Tools > Secrets), não através da interface. A página apenas mostra o status e permite testar conexões.

## Mudanças Recentes
- 2026-01-20: Aplicação criada com todas as funcionalidades
- 2026-01-20: Corrigido serialização UserResponse (from_attributes)
- 2026-01-20: Admin bootstrap via variáveis de ambiente
- 2026-01-20: Adicionado painel de gerenciamento de integrações
