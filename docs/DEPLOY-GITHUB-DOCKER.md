# Deploy: GitHub + Docker — Servidor Interno

Plano para migrar o Agente IA - RV do Replit para um servidor interno da empresa com domínio próprio.

## Pré-requisitos

- Servidor Linux com Docker e Docker Compose instalados
- Domínio configurado (DNS apontando para o IP do servidor)
- Certificado SSL (Let's Encrypt via Certbot ou Traefik)
- PostgreSQL 16 com extensão pgvector
- Acesso às APIs: OpenAI, Z-API, Tavily, Microsoft Entra ID (SSO)

## Etapa 1: Conectar Replit ao GitHub

1. No Replit, abrir o painel **Git** (ícone de branch na sidebar)
2. Clicar em **Connect to GitHub**
3. Autorizar o Replit na conta GitHub da organização
4. Criar repositório privado (ex: `svn-agente-ia-rv`)
5. Push do código atual para o repo
6. Verificar que `.gitignore` inclui: `__pycache__/`, `*.pyc`, `.env`, `data/uploads/`, `node_modules/`

## Etapa 2: Dockerfile (Produção)

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN useradd -m -u 1000 appuser

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc libmagic1 libmupdf-dev ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

CMD ["gunicorn", "main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:5000", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
```

**Nota:** Com Docker, o `--start-period=40s` dá 40 segundos para o app iniciar antes de começar health checks. Isso elimina completamente o problema de cold start do Replit.

## Etapa 3: docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build: .
    container_name: agente-ia-rv
    restart: unless-stopped
    env_file: .env
    expose:
      - "5000"
    depends_on:
      db:
        condition: service_healthy
    networks:
      - app-network
    volumes:
      - uploads:/app/data/uploads

  db:
    image: ankane/pgvector:v0.7.4-pg16
    container_name: agente-ia-db
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - app-network

  nginx:
    image: nginx:1.27-alpine
    container_name: agente-ia-proxy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - app
    networks:
      - app-network

volumes:
  pgdata:
  uploads:

networks:
  app-network:
    driver: bridge
```

## Etapa 4: nginx.conf

```nginx
upstream app {
    server app:5000;
}

server {
    listen 80;
    server_name SEU_DOMINIO.com.br;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name SEU_DOMINIO.com.br;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    client_max_body_size 50M;

    location / {
        proxy_pass http://app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://app;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Etapa 5: Variáveis de Ambiente (.env)

```env
DATABASE_URL=postgresql://USER:PASSWORD@db:5432/DBNAME
OPENAI_API_KEY=sk-...
ZAPI_INSTANCE_ID=...
ZAPI_TOKEN=...
ZAPI_CLIENT_TOKEN=...
TAVILY_API_KEY=tvly-...
MICROSOFT_CLIENT_ID=...
MICROSOFT_CLIENT_SECRET=...
MICROSOFT_TENANT_ID=...
SESSION_SECRET=...
ALLOWED_ORIGINS=https://SEU_DOMINIO.com.br
```

## Etapa 6: CI/CD com GitHub Actions (opcional)

Criar `.github/workflows/deploy.yml` para deploy automático via SSH no servidor:

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /opt/agente-ia-rv
            git pull origin main
            docker compose build --no-cache
            docker compose up -d
            docker compose logs --tail=20 app
```

## Etapa 7: Deploy no Servidor

```bash
ssh usuario@servidor
cd /opt/agente-ia-rv
git clone https://github.com/ORG/svn-agente-ia-rv.git .
cp .env.example .env  # Editar com valores reais
mkdir -p nginx/ssl     # Colocar certificados SSL
docker compose up -d
docker compose logs -f app  # Verificar startup
```

## Diferenças Replit vs Docker

| Aspecto | Replit | Docker (servidor próprio) |
|---------|--------|--------------------------|
| Health check startup | 5s fixo (problemático) | 40s configurável |
| Cold start | Sim (autoscale) | Não (always running) |
| Background threads | Requer VM ($) | Nativo |
| SSL | Automático | Certbot/Traefik |
| Domínio | *.replit.app | Próprio |
| Controle | Limitado | Total |
| Custo | $7-20/mês | Servidor existente |
| pgvector | Disponível | Via imagem ankane/pgvector |

## Notas Importantes

- **O pre-startup socket compartilhado NÃO é necessário no Docker** — o health check tem `--start-period=40s`, dando tempo suficiente para o app iniciar.
- **Gunicorn** substitui uvicorn direto: gerencia workers, restart automático, melhor para produção.
- **O SSO Microsoft** precisa ter o redirect URI atualizado para o novo domínio no Azure AD.
- **O Z-API webhook** precisa ser reconfigurado para apontar para o novo domínio.
