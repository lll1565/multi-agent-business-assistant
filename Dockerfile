FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_ENV=production \
    LOG_FORMAT=json \
    UVICORN_HOST=0.0.0.0 \
    DATA_DIR=/app/data \
    DB_PATH=/app/data/demo.db \
    CHAT_DB_PATH=/app/data/chat.db

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends graphviz \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src
COPY scripts/docker_entrypoint.sh /entrypoint.sh

RUN pip install -e . \
    && chmod +x /entrypoint.sh \
    && mkdir -p /app/data/logs /app/data/diagrams

EXPOSE 8010

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8010/api/health', timeout=3)"

ENTRYPOINT ["/entrypoint.sh"]
CMD ["multi-agent-backend"]
