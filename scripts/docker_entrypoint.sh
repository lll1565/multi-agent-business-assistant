#!/bin/sh
set -e

if [ ! -f /app/data/demo.db ]; then
  echo "[entrypoint] initializing demo.db ..."
  multi-agent-init-demo || true
fi

mkdir -p /app/data/logs /app/data/diagrams

exec "$@"
