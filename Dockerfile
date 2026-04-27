FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN useradd -m -u 1000 appuser

WORKDIR /app

# System libs:
#  - libpq-dev: psycopg2 (PostgreSQL)
#  - libmagic1: python-magic (sniff de tipo de arquivo)
#  - ffmpeg: conversão de áudio do WhatsApp
#  - poppler-utils, ghostscript: pdf2image / pdf rasterização
#  - libcairo2-dev, libmupdf-dev, mupdf-tools: pymupdf
#  - libfreetype6-dev, libjpeg62-turbo-dev, libpng-dev, libtiff-dev, libwebp-dev: Pillow
#  - libxml2-dev, libxslt-dev: lxml (fallback caso wheel não exista)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    libmagic1 \
    ffmpeg \
    poppler-utils \
    ghostscript \
    libcairo2-dev \
    libmupdf-dev \
    mupdf-tools \
    libfreetype6-dev \
    libjpeg62-turbo-dev \
    libpng-dev \
    libtiff-dev \
    libwebp-dev \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .

# ----------------------------------------------------------------------------
# Versionamento da imagem (Defesa #4): grava o SHA do commit em /app/VERSION
# para o endpoint /health expor qual revisão está rodando em produção.
#
# Railway injeta a env RAILWAY_GIT_COMMIT_SHA automaticamente em todo build,
# mas para manter compatibilidade com `docker build` local também aceitamos
# `--build-arg GIT_SHA=...`. Se nenhum dos dois estiver presente, gravamos
# "unknown" para não quebrar o build — o /health continua funcional.
# ----------------------------------------------------------------------------
ARG GIT_SHA=""
ARG BUILD_TIMESTAMP=""
RUN echo "${GIT_SHA:-${RAILWAY_GIT_COMMIT_SHA:-unknown}}" > /app/VERSION && \
    echo "${BUILD_TIMESTAMP:-$(date -u +%Y-%m-%dT%H:%M:%SZ)}" > /app/BUILD_TIMESTAMP && \
    chown appuser:appuser /app/VERSION /app/BUILD_TIMESTAMP

# ----------------------------------------------------------------------------
# NOTA (Defesa #2): a chamada `RUN pytest tests/test_structure_guard.py -q`
# foi REMOVIDA do build em 27/04/2026 (Task #179). Ela ficava aqui para
# garantir a guarda anti-captura de estrutura (POP/Collar/Fence/COE), mas
# build-time tests dentro do container são frágeis e foram a causa
# provável da fila de 15+ deploys travados desde 23/04.
#
# A guarda CONTINUA viva em `tests/test_structure_guard.py` e DEVE ser
# rodada localmente antes de cada `git push` via:
#
#     bash scripts/preflight.sh
#
# Ou, se preferir, configure um GitHub Actions com `pytest tests/`.
# ----------------------------------------------------------------------------

RUN mkdir -p /app/uploads/materials /app/uploads/attachments && \
    chown -R appuser:appuser /app/uploads

USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT:-5000}/health')" || exit 1

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-5000}"]
