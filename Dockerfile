# Multi-stage production image — API + built frontend on port 8010

FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_ENV=production \
    SERVE_FRONTEND=true \
    LOG_FORMAT=json \
    UVICORN_HOST=0.0.0.0

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends graphviz \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --upgrade pip && pip install -e .

COPY --from=frontend-build /app/frontend/dist ./frontend/dist
COPY scripts/docker_entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN mkdir -p /app/data/logs /app/data/diagrams

EXPOSE 8010

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8010/api/health', timeout=3)"

ENTRYPOINT ["/entrypoint.sh"]
CMD ["multi-agent-backend"]
