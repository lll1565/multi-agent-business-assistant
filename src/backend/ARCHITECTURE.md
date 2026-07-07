# Backend 架构说明

FastAPI 后端采用**六边形架构（端口-适配器）**：HTTP 层只依赖抽象端口，Agent 与数据库通过适配器注入，便于测试替换与边界隔离。

## 分层图

```
HTTP 请求
    │
    ▼
api/v1/              路由、参数校验、Depends 注入
    │
    ▼
services/            业务编排（聊天、会话 CRUD）
    │
    ├──► ports/agent.py          AgentPort 抽象
    │         │
    │         ▼
    │    adapters/stone_agent.py  StoneAgentService → subagent.stone
    │
    └──► repositories/            SessionRepository 抽象
              │
              ▼
         infrastructure/database/   SQLAlchemy Engine + ORM
              │
              ▼
         data/chat.db              会话与消息持久化

app/factory.py       FastAPI 装配、中间件、生命周期
app/container.py     DI 容器（build_container）
domain/entities.py   领域实体（Session / Message）
schemas/             Pydantic API 契约（OpenAPI）
core/                无业务依赖工具（响应壳、异常；paths 请用 config.paths）
config/              Backend 专属配置（见下）
```

## 依赖方向

| 层 | 可依赖 | 不可依赖 |
|----|--------|----------|
| `api/` | `services`、`schemas`、`app.container` | `adapters` 具体实现（经 Depends） |
| `services/` | `ports`、`repositories`、`domain` | `api/` |
| `repositories/` | `infrastructure`、`domain` | `services/` |
| `adapters/` | `subagent.*`、`ports` | `api/` |
| `subagent/` | 自身 | **`backend`（import-linter 强制）** |

Backend 可单向依赖 `subagent`（例如 `factory` 读取 checkpoint 路径、`StoneAgentService` 调用 Supervisor）。Agent 层不得 import `backend`。

## 配置

| 模块 | 用途 |
|------|------|
| `backend/config/settings.py` | chat DB、CORS、线程池、日志、tracing、端口 |
| `backend/config/paths.py` | 聊天库路径、项目根、data 目录 |
| `backend/config/ports.json` | dev 端口（后端 / 前端 / Vite / 脚本共用） |
| `backend/config/logging_setup.py` / `tracing.py` / `structured_log.py` | 后端日志与可观测性 |
| `subagent/config/settings.py` | LLM、路由、业务 DB、日志 |
| `subagent/config/paths.py` | demo 库、checkpoint 路径 |
| `subagent/config/demo_db.py` | 业务演示库初始化 |
| `subagent/config/logging_setup.py` / `tracing.py` | Agent 侧日志与 span |

Agent 使用 `subagent.config.*`；Backend 使用 `backend.config.*`。二者读取同一份项目根 `.env`，但代码完全分离。

```python
# Agent 层
from subagent.config.settings import get_agent_settings

# Backend 层
from backend.config.settings import get_backend_settings
```

## 路径

**约定：Backend 一律从 `backend.config.paths` 导入路径解析函数。**

- `subagent.config.paths.resolve_demo_db_path()` → `data/demo.db`
- `backend.config.paths.resolve_chat_db_path()` → `data/chat.db`
- `subagent.config.paths.resolve_checkpoint_db_path()` → `data/agent_checkpoints.db`

## 统一响应与可观测性

- 所有 API 返回 `ApiResponse[T]`（`backend/core/response.py`）
- `request_logging_middleware` 注入 `request_id`，结构化日志见 `backend/config/structured_log.py`
- OTEL / LangSmith：`backend/config/tracing.py` 在 lifespan 启动时配置；响应头可带 `X-Trace-Id`

## 启动

```powershell
.\scripts\run_backend.ps1
# 或
multi-agent-backend
# 或
uvicorn backend.main:app --host 127.0.0.1 --port 8010
```

端口默认值见 `backend/config/ports.json`。Agent checkpoint 使用共享 SQLite，**建议单 worker**（`workers=1`）。

## 测试边界

`tests/backend/test_architecture.py` 通过 import-linter 断言 `subagent ↛ backend`。
