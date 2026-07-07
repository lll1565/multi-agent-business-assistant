# Multi-Agent Chat System

基于 LangGraph / Deep Agents 的多智能体聊天系统：**LLM 后端为 MiniMax M3**（OpenAI 兼容 API，`https://api.minimaxi.com/v1`）。一个 **Supervisor Agent**（stone）按需调度多个**领域子 Agent**（db / api / web / diagram）。子 Agent 通过**注册中心模式**自动发现，新增能力**无需改动核心代码**。

---

## 架构概览

```
用户
  │
  ▼
Vue 3 前端  (http://localhost:5143，端口见 src/backend/config/ports.json)
  │
  ▼ HTTP/JSON
FastAPI 后端  (http://127.0.0.1:8010,Swagger: /api/docs)
  │
  ▼
StoneAgentService  ──►  src/subagent/stone/core.py  (Supervisor)
                          │
                          │ SubAgentRegistry.discover_stone_agents()
                          ▼
                        ┌─────────────┬─────────────┬─────────────┬─────────────┐
                        │ npi_db_agent│ npi_api_agent│npi_web_agent│npi_diagram_ │
                        │   (db)      │   (api)      │   (web)     │   agent     │
                        └─────────────┴─────────────┴─────────────┴─────────────┘
                              │              │              │              │
                              ▼              ▼              ▼              ▼
                       data/demo.db    API 文档        DuckDuckGo      Graphviz
                       (SQL)          (本地 JSON)       (网页搜索)     (DOT 渲染)
```

后端内部分层（详见 [`src/backend/ARCHITECTURE.md`](src/backend/ARCHITECTURE.md)）:

```
api/v1/              HTTP 路由、参数校验
    ↓ Depends
services/            业务编排（聊天、会话 CRUD）
    ├──► ports/agent.py          AgentService 抽象
    │         ↓
    │    adapters/stone_agent.py StoneAgentService → subagent.stone
    └──► repositories/           SessionRepository 抽象
              ↓
         infrastructure/database/ SQLAlchemy Engine + ORM
              ↓
         data/chat.db

app/factory.py       FastAPI 装配、中间件、生命周期
app/container.py     DI 容器（build_container）
domain/entities.py   领域实体（Session / Message）
schemas/             Pydantic API 契约（OpenAPI Schema）
core/                无业务依赖工具（ApiResponse、异常；路径见 config/paths）
config/              Backend 配置（ports / paths / settings / logging）
```

项目专属术语见 [`docs/GLOSSARY.md`](docs/GLOSSARY.md)。

---

## 三个数据库的边界

| 文件 | 用途 | 写入方 | 说明 |
|------|------|--------|------|
| `data/demo.db` | 业务演示数据 | `multi-agent-init-demo` 或 `scripts/demo_db.py` | npi_db_agent 查询的目标,模拟生产库；**clone 后首次使用前必须初始化** |
| `data/chat.db` | 会话元数据 + 消息历史 | `repositories/`(FastAPI) | 前后端展示用 |
| `data/agent_checkpoints.db` | LangGraph Checkpoint | `subagent/stone/core.py` | Agent 多轮对话记忆 |

**为什么 checkpoint 要独立成库?**

- LangGraph 在每次 Agent 节点跳转时写 checkpoint，**写频率远高于聊天消息**
- 与 `data/chat.db` 隔离后，删除会话时 Backend 会调用 `delete_session_checkpoints()` 清理对应 thread（supervisor + 已注册 db/api 子 Agent），不会拖累业务库
- 业务库做备份/迁移时，不需要带上一堆 checkpoint blob

**部署注意：** Agent 使用 `@lru_cache` 单例 + 共享 SQLite checkpoint，**请用单 worker 运行 uvicorn**（`workers=1`）。若设置 `UVICORN_WORKERS` / `WEB_CONCURRENCY` 大于 1，后端启动时会 **fail-fast** 直接报错。监听地址见 `src/backend/config/ports.json` 的 `uvicorn_host`（`backend/main.py` 与脚本共用）。

---

## 目录结构

```
multi_agent_system/
├── src/
│   ├── subagent/
│   │   ├── config/               ← Agent 配置(settings / paths / logging / demo_db)
│   │   └── stone/                ← Supervisor + 子 Agent
│   │       ├── routing/          ← 注册中心、分类、快路径、硬路由
│   │       ├── runtime/          ← 执行、流式、trace、core/cli 入口
│   │       ├── persistence/      ← checkpoint、SQL 工具
│   │       ├── safety.py         ← 横切安全规则
│   │       ├── core.py / cli.py  ← 向后兼容 shim
│   │       └── npi_*_agent/      ← 每个子 Agent 一个目录
│   │           ├── AGENTS.md
│   │           ├── __init__.py   ← AGENT_SPEC
│   │           ├── sub_agent.py
│   │           ├── tools.py
│   │           └── skills/       ← (可选)工作流技能
│   └── backend/                  ← FastAPI 后端（src layout）
│       ├── api/v1/
│       ├── services/
│       ├── repositories/
│       ├── infrastructure/database/
│       ├── domain/entities.py
│       ├── schemas/
│       ├── adapters/             ← StoneAgentService
│       ├── ports/
│       ├── app/
│       ├── core/
│       ├── config/               ← ports.json / paths / settings
│       ├── ARCHITECTURE.md
│       └── main.py
├── docs/                         ← GLOSSARY.md 等项目文档
├── frontend/                     ← Vue 3 (Vite)
├── tests/                        ← pytest（agent / backend / integration）
├── data/                         ← 运行时数据（不入库）
├── .github/workflows/ci.yml
├── pyproject.toml
└── scripts/                      ← run_*.ps1、demo_db.py
```

---

## 安装与启动

### 前置

- Python ≥ 3.11
- Node.js ≥ 18(前端)
- 可选:`graphviz`(`dot` 命令,用于 npi_diagram_agent 渲染 PNG)

### 1. 创建虚拟环境并安装依赖

```powershell
cd D:\pythonStudy\baozun\ai_study\multi_agent_system
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]" --index-url https://pypi.org/simple
.\.venv\Scripts\python.exe -m pre_commit install   # 可选：启用提交前 ruff/mypy 钩子
```

> 安装后 `subagent`、`backend` 都是顶层包，可以直接 `from backend.main import app`。

### 2. 配置环境变量

```powershell
copy .env.example .env
# 编辑 .env，填入 OPENAI_API_KEY（必需）
```

**安全提示：**

- `.env` 已在 `.gitignore` 中，**切勿** `git add .env`
- 若密钥曾出现在对话/日志中，请在 MiniMax 控制台**轮换/作废**后更新本地 `.env`
- 仓库内只保留 `.env.example`（占位符，无真实密钥）

启动前**务必清代理变量**(Windows 上 VPN/Clash 常驻会干扰 LLM 调用):

```powershell
Remove-Item Env:HTTP_PROXY, HTTPS_PROXY, http_proxy, https_proxy -ErrorAction SilentlyContinue
```

**路径与部署相关变量（可选）：**

| 变量 | 说明 |
|------|------|
| `PROJECT_ROOT` | 仓库根目录；`pip install -e .` 开发环境通常不用设；wheel 安装或自定义部署目录时**建议设置** |
| `DATA_DIR` | 运行时数据根（默认 `$PROJECT_ROOT/data`），checkpoint / chat.db / demo.db / logs 均在其下 |
| `REPLY_BUFFER_CHUNK_SIZE` | SSE 回复缓冲分块大小（应用层，**不是** LLM token stream chunk）；旧名 `STREAM_DELTA_CHUNK_SIZE` 仍兼容 |

`.env.example` 中有完整示例。

### 3. 初始化业务库

```powershell
.\.venv\Scripts\python.exe scripts/demo_db.py
# 或: multi-agent-init-demo
```

### 4. 启动

**权威入口（按场景）：**

| 场景 | 推荐命令 | 说明 |
|------|----------|------|
| Windows 日常开发 | `.\scripts\run_all.ps1` | 一键启后端 + 前端，带健康检查 |
| Linux/macOS 或分终端 | `make backend` + `make frontend` | Makefile 等价启动 |
| 生产 / wheel 安装 | `multi-agent-backend` 或 `docker compose up` | 无 reload、workers=1；详见 [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) |
| CLI 烟囱测试 | `multi-agent-cli` | 不经过 FastAPI，直接调 Supervisor |

**Windows 细粒度脚本：**

| 场景 | 命令 | 效果 |
|------|------|------|
| 只启后端 | `.\scripts\run_backend.ps1` | http://127.0.0.1:8010，Swagger `/api/docs` |
| 生产后端 | `.\scripts\run_backend_prod.ps1` | 无 reload，`LOG_FORMAT=json` |
| 只启前端 | `.\scripts\run_frontend.ps1` | http://127.0.0.1:5143（见 `src/backend/config/ports.json`） |
| 全部停止 | `.\scripts\stop_all.ps1` | 清理 uvicorn / vite 进程 |

后端日志写在 `data/logs/`,前端日志在 `data/logs/frontend.*.log`。

### 开发者命令速查

| 命令 | 说明 |
|------|------|
| `make install-dev` | 安装 Python 开发依赖 |
| `make test` | pytest（临时文件写入 `tests/.tmp/`，已在 `.gitignore`） |
| `make lint` / `make format-check` | ruff check / format --check（`src/backend` + `src/subagent` + `tests`） |
| `make typecheck` | mypy backend + stone 路由核心模块 |
| `make arch-test` | import-linter 架构契约 |
| `make frontend-test` | vitest 前端单测 |
| `make ci` | 本地跑齐 CI 等价检查 |
| `pre-commit run --all-files` | 提交前本地检查（需先 `pip install pre-commit && pre-commit install`） |

**CLI 入口：**

| 命令 | 说明 |
|------|------|
| `multi-agent-backend` | 生产 FastAPI 启动（uvicorn workers=1） |
| `multi-agent-cli` / `python -m subagent.stone.cli` | 不经过 FastAPI，直接调 Supervisor |
| `python -m subagent.stone.core "问题"` | 同上，可传参（开发调试用） |
| `multi-agent-init-demo` | 初始化 `data/demo.db` |

**给 LLM / IDE 读的文档：**

- [`docs/GLOSSARY.md`](docs/GLOSSARY.md) — Stone / NPI / 三库 / console_scripts 术语表
- 根目录 [`skill.md`](skill.md) — 项目目录与架构速览（Codex / Cursor 用）
- [`src/subagent/stone/AGENTS.md`](src/subagent/stone/AGENTS.md) — Supervisor 角色说明
- 各 `npi_*_agent/AGENTS.md` — 子 Agent 角色卡
- `skills/*/SKILL.md` — 工作流技能说明

---

## 如何新增一个子 Agent

目标:**只新增一个 `npi_xxx_agent/` 文件夹就能上线新能力**,不用改 `core.py` / `routing.py`。

### 1. 建子目录

```
src/subagent/stone/npi_xxx_agent/
├── AGENTS.md       # 给 LLM 看的角色说明(中文)
├── __init__.py     # 导出 create_npi_xxx_agent + AGENT_SPEC
├── sub_agent.py    # create_npi_xxx_agent() 工厂(用 @lru_cache)
├── tools.py        # @tool 工具列表
└── skills/<skill>/SKILL.md   # (可选)工作流技能文档
```

### 2. 写工厂

```python
# src/subagent/stone/npi_xxx_agent/sub_agent.py
from functools import lru_cache
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain_openai import ChatOpenAI

from subagent.config.settings import get_agent_settings

settings = get_agent_settings()
from .tools import get_xxx_tools


@lru_cache(maxsize=1)
def create_npi_xxx_agent():
    return create_deep_agent(
        model=ChatOpenAI(model=settings.openai_model, temperature=0),
        memory=[__file__.replace("sub_agent.py", "AGENTS.md")],
        tools=get_xxx_tools(),
        subagents=[],
        backend=FilesystemBackend(root_dir=__file__.rsplit("/", 1)[0], virtual_mode=True),
        name="npi_xxx_agent",
    )
```

### 3. 声明 AGENT_SPEC(关键 — 只有这一步是手写的)

```python
# src/subagent/stone/npi_xxx_agent/__init__.py
from .sub_agent import create_npi_xxx_agent
from subagent.stone.routing.registry import SubAgentSpec

AGENT_SPEC = SubAgentSpec(
    name="npi_xxx_agent",
    description="给 Supervisor LLM 看的描述,用于触发委派",
    factory=create_npi_xxx_agent,
    keywords=("xxx", "你的领域词", __import__("re").compile(r"正则.*也行")),
    kind="xxx",
    supports_hard_route=False,   # 可直跳子 Agent 的高置信场景
    supports_fast_path=False,    # 无 LLM 快速通道(需要纯 query_xxx 工具)
    capability_title="你的能力名称",  # 「你能做什么」里展示的分节标题
    capability_bullets=("能力说明 1", "能力说明 2"),
    capability_examples=("示例问法 1", "示例问法 2"),
    capability_order=50,         # 列表排序，数字越小越靠前
)

__all__ = ["create_npi_xxx_agent", "AGENT_SPEC"]
```

`registry.discover_stone_agents()` 在首次启动时会扫描 `src/subagent/stone/` 下所有 `npi_*_agent/`,把 `AGENT_SPEC` 自动注册到 `SubAgentRegistry`。**`core.py` / `routing.py` / `hard_route.py` / `api_fastpath.py` / `meta_fastpath.py` 都不用动**——用户问「你能做什么」时，能力说明会从注册中心自动生成。

---

## 已落地的子 Agent

| Agent | kind | 工具 | 触发词 |
|-------|------|------|--------|
| `npi_db_agent` | db | `sql_db_*`(LangChain SQLDatabaseToolkit) | 数据库 / SQL / 订单 / 客户 |
| `npi_api_agent` | api | `query_api_doc`, `list_all_apis` | 接口 / get_users / REST |
| `npi_web_agent` | web | `search_web`(DuckDuckGo,零 API key) | 搜索 / 网上 / 互联网 |
| `npi_diagram_agent` | diagram | `render_diagram`(Graphviz + 降级) | 画 / 流程图 / 架构图 |

新增第 5 个 agent 的步骤与上面 4 个完全一致。

---

## 路由策略(四层降级)

1. **元问题快速通道**(`routing/meta_fastpath.py`):问"你是谁 / 你能做什么 / 帮助"→ 模板回复,**不调 LLM**。
2. **API 文档快速通道**(`routing/api_fastpath.py`):明确的 API 文档问题 → 直接查本地文档,**不调 LLM**。
3. **DB 硬路由**(`routing/hard_route.py`):明确的 DB/SQL 问题 → 跳过 Supervisor 直接委派 `npi_db_agent`。
4. **Supervisor LLM 委派**(`runtime/core.py`):模糊或混合问题 → 主 Agent 推理 + 委派。

四层判定都基于 `SubAgentSpec` 中的 `keywords` / `exclusive_keywords` / `exclusive_cancel_keywords` / `supports_hard_route` / `supports_fast_path` 字段,**新增 Agent 时只需填好这些字段就能复用整套流水线**。

---

## 测试

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pytest tests/agent/test_registry.py -q   # 注册中心
.\.venv\Scripts\python.exe -m pytest tests/agent/test_routing.py -q    # 路由分类
.\.venv\Scripts\python.exe -m pytest tests/agent/test_golden_routes.py -q  # golden 路由
.\.venv\Scripts\python.exe -m ruff check src/backend src/subagent tests
.\.venv\Scripts\python.exe -m mypy backend
.\.venv\Scripts\python.exe -m mypy src/subagent/stone/routing/registry.py src/subagent/stone/routing/classifier.py src/subagent/stone/routing/routing_intents.py src/subagent/stone/routing/routing_types.py src/subagent/stone/routing/api_fastpath.py src/subagent/stone/persistence/checkpointer.py src/subagent/stone/routing/hard_route.py src/subagent/stone/routing/resolve_route.py src/subagent/stone/runtime/core.py src/subagent/stone/runtime/turn_runner.py
cd frontend
npm run lint
npm run typecheck
npm run build
```

Windows 上若 `%TEMP%\pytest-of-*` 权限异常，pytest 已配置 `--basetemp=tests/.tmp`（见 `pyproject.toml`）。

CI（GitHub Actions）在 push/PR 时自动跑 pytest、ruff、mypy（backend + stone 路由核心）、import-linter、ESLint、Typecheck 与前端 build。

### 可观测性（LangSmith + OpenTelemetry）

| 变量 | 说明 |
|------|------|
| `LANGSMITH_TRACING=true` | 开启 LangChain/LangGraph 调用链（需 `LANGSMITH_API_KEY`） |
| `OTEL_ENABLED=true` | 开启 HTTP + Agent OTEL span（响应头 `X-Trace-Id`） |
| `OTEL_EXPORTER_ENDPOINT` | OTLP HTTP 端点；未设则输出到控制台 |
| `LOG_FORMAT=json` | 日志一行一条 JSON（含 `request_id` / `trace_id`） |

安装 OTEL 依赖：`pip install -e ".[tracing]"`

### 端口配置

开发与脚本共用 **`src/backend/config/ports.json`**（后端 8010、前端 5143）。修改后重启服务即可；Vite 与 PowerShell 启动脚本均读取该文件。

---

## 已知问题 / 后续 TODO

- `npi_db_agent` / `npi_api_agent` 中 prompt 与关键字的中英文混排，正则匹配对繁体/英文 query 命中率待验证。
- 跨 Agent 的 cancel 词已收敛到 `subagent/stone/routing/routing_intents.py`；**新增 API 端点名或 DB 表名时请只改该文件**。
- `classify_query()` 为遗留接口（仅 db/api/both）；新代码请用 `classify_query_agents()`。
- `langchain-community` 已从依赖移除；SQL 工具使用 `subagent.stone.tools.database.SqlDb`（SQLAlchemy 实现）。

---

## 注意

- 启动后端前确认 `HTTP_PROXY` / `HTTPS_PROXY` 已清,否则会 `Connection error`
- 生产环境请配置 `CORS_ORIGINS` 白名单,别用 `*`
- 日志路径在 `data/logs/`,SQLite 数据库在 `data/`(均已在 `.gitignore`)
