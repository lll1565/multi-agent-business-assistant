# 生产部署指南

本文说明如何将 Multi-Agent Chat System 部署到单机/内网生产环境。当前架构为 **SQLite 三库 + 单 Uvicorn worker**，适合 PoC、内网工具或中小流量场景。

---

## 架构约束

| 项 | 生产建议 |
|----|----------|
| Worker 数 | **必须为 1**（LangGraph SQLite checkpoint 共享） |
| 数据库 | 默认 SQLite；高并发需迁移 Postgres checkpoint（见文末演进） |
| 前端 | Docker 镜像内已构建，`SERVE_FRONTEND=true` 时由 FastAPI 托管 |
| LLM | 需配置 `OPENAI_API_KEY`（MiniMax 兼容 OpenAI API） |

---

## 1. 环境变量

复制并编辑 `.env`：

```bash
cp .env.example .env
```

**生产最小配置：**

```env
APP_ENV=production
OPENAI_API_KEY=your_key
OPENAI_BASE_URL=https://api.minimaxi.com/v1
OPENAI_MODEL=MiniMax-M2.7

API_AUTH_KEY=change-me-to-a-long-random-string
CHAT_RATE_LIMIT_PER_MINUTE=30

CORS_ORIGINS=https://your-domain.example
TRUSTED_HOSTS=your-domain.example,localhost

SERVE_FRONTEND=true
LOG_FORMAT=json
LOG_LEVEL=INFO

DATA_DIR=/app/data
```

| 变量 | 说明 |
|------|------|
| `APP_ENV=production` | 启用生产检查（如 `/api/ready` 要求 API Key） |
| `API_AUTH_KEY` | 非空时，除 health/ready/docs 外需 `X-API-Key` 或 `Authorization: Bearer` |
| `CHAT_RATE_LIMIT_PER_MINUTE` | 每 IP 每分钟聊天请求上限，`0` 关闭 |
| `TRUSTED_HOSTS` | Host 头白名单，防 Host Header 攻击 |
| `SERVE_FRONTEND` | 托管 `frontend/dist` 静态资源 |
| `DATA_DIR` | 运行时数据根（三库 + 日志） |

前端构建时传入 API Key（与后端 `API_AUTH_KEY` 一致）：

```bash
cd frontend && VITE_API_KEY=your-key npm run build
```

Docker 镜像在构建阶段已执行 `npm run build`；若需 Key，在 Dockerfile 中增加 `ARG VITE_API_KEY` 或在 compose 中重建。

---

## 2. Docker Compose（推荐）

```bash
# 1. 配置 .env（含 OPENAI_API_KEY、API_AUTH_KEY）
docker compose build
docker compose up -d

# 2. 访问
# UI + API: http://localhost:8010
# Swagger:  http://localhost:8010/api/docs
```

数据持久化在 `./data` 卷（chat / demo / checkpoint / logs）。

**健康检查：**

- Liveness: `GET /api/health` — 进程存活
- Readiness: `GET /api/ready` — LLM Key、chat 库、checkpoint 目录

---

## 3. 裸机 / VM 部署

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
pip install -e .
multi-agent-init-demo

cd frontend && npm ci && VITE_API_KEY=xxx npm run build && cd ..

export APP_ENV=production SERVE_FRONTEND=true LOG_FORMAT=json
multi-agent-backend
```

Windows 等价脚本：`.\scripts\run_backend_prod.ps1`

Makefile：`make backend-prod`

---

## 4. 反向代理（Nginx 示例）

若前后端分域部署，前端 `npm run build` 后由 Nginx 托管静态文件，API 反代到 8010：

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8010;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-API-Key $http_x_api_key;
    proxy_buffering off;   # SSE 必须关闭缓冲
}

location / {
    root /var/www/multi-agent/frontend/dist;
    try_files $uri $uri/ /index.html;
}
```

---

## 5. 安全清单

- [ ] 设置强随机 `API_AUTH_KEY`
- [ ] `CORS_ORIGINS` 不要用 `*`
- [ ] 生产设置 `TRUSTED_HOSTS`
- [ ] 启用 `CHAT_RATE_LIMIT_PER_MINUTE` 防止 LLM 成本失控
- [ ] `.env` 不入库；密钥轮换后更新
- [ ] 启动前清除代理变量（见 README）

---

## 6. 运维命令

| 命令 | 用途 |
|------|------|
| `multi-agent-backend` | 生产启动（无 reload，workers=1） |
| `multi-agent-init-demo` | 初始化/刷新业务演示库 |
| `multi-agent-cli "问题"` | CLI 烟囱测试（不经 HTTP） |
| `make ci` | 本地跑齐 CI 检查 |

---

## 7. 生产演进路线（可选）

当前 SQLite 方案有意为之。若流量/可靠性要求提高：

1. **Checkpoint** → `langgraph-checkpoint-postgres` + Postgres
2. **Chat DB** → PostgreSQL（改 `engine.py` URL + Alembic 迁移）
3. **Worker** → checkpoint 迁移后可评估多 worker + 队列
4. **长期记忆** → 向量库（pgvector / Qdrant）+ 抽取 pipeline
5. **Observability** → 已有 LangSmith / OTEL 钩子，生产打开即可

---

## 8. 故障排查

| 现象 | 排查 |
|------|------|
| `/api/ready` 503 | 看 `checks` 数组：`llm_api_key` / `chat_database` |
| 401 未授权 | 前端需带 `X-API-Key`；health/ready 无需 Key |
| 429 限流 | 调大 `CHAT_RATE_LIMIT_PER_MINUTE` 或关为 0 |
| Agent 无记忆 | 确认 `data/agent_checkpoints.db` 卷持久化 |
| 多 worker 启动失败 | 预期行为；保持 `workers=1` |

日志：`data/logs/app.log`；Docker 内同路径（挂载卷可见）。
