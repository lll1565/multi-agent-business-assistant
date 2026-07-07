# 项目术语表

本仓库使用的专有名词与命名约定，供新成员与 LLM 工具快速对齐。

---

## Stone

| 名称 | 含义 |
|------|------|
| **Stone** | 项目品牌名 / Supervisor 代号。README 架构图中的 `StoneAgentService` 指后端适配器类；Python 包名为小写 `stone`（`src/subagent/stone/`）。 |
| **stone 模块** | Supervisor（主调度 Agent）及其路由、注册、流式等核心逻辑，入口为 `core.py`。 |
| **StoneAgentService** | `backend/adapters/stone_agent.py` 中的类，实现 `ports/agent.py` 的 `AgentService` 接口，将 HTTP 层请求转发给 `subagent.stone`。 |

**约定：** 文档与类名用 **Stone**（PascalCase）；import 路径用 **`subagent.stone`**（小写包名）。

---

## NPI

| 名称 | 含义 |
|------|------|
| **NPI** | **New Product Introduction**（新产品导入）的缩写，本项目业务域代号。 |
| **npi_ 前缀** | 子 Agent 包命名模板：`npi_<domain>_agent`，例如 `npi_db_agent`、`npi_api_agent`。 |
| **npi_db_agent** | 数据库 / SQL 查询子 Agent，读写 `data/demo.db`。 |
| **npi_api_agent** | REST API 文档查询子 Agent，读本地 JSON 文档。 |
| **npi_web_agent** | 网页搜索子 Agent（DuckDuckGo）。 |
| **npi_diagram_agent** | 流程图 / 架构图渲染子 Agent（Graphviz DOT）。 |

**约定：** 新增子 Agent 时目录名、工厂函数、`AGENT_SPEC.name` 均使用 `npi_<domain>_agent` 格式；`registry.discover_stone_agents()` 会自动扫描 `stone/npi_*_agent/`。

---

## 三个数据库

| 文件 | 别名 | 用途 | 初始化 |
|------|------|------|--------|
| `data/demo.db` | 业务库 | npi_db_agent 查询的演示数据，模拟生产库 | `multi-agent-init-demo` |
| `data/chat.db` | 会话库 | FastAPI 持久化会话与消息历史 | 首次启动后端自动创建 |
| `data/agent_checkpoints.db` | Checkpoint 库 | LangGraph 多轮对话记忆 | 首次 Agent 调用时自动创建 |

三者职责分离：checkpoint 写频率高，与业务/会话库隔离，便于备份与清理。

---

## stone 子包

| 包 | 职责 | 主要模块 |
|----|------|----------|
| `stone/routing/` | 路由与注册 | `registry`、`classifier`（原 routing.py）、`resolve_route`、快路径、硬路由 |
| `stone/runtime/` | 执行与流式 | `core`、`turn_runner`、`agent_factory`、`streaming/`、`trace`、`contracts` |
| `stone/persistence/` | 持久化 | `checkpointer`、`tools/`（SQL 工具） |
| `stone/safety.py` | 横切安全规则 | SQL 校验、Agent spec 约束 |
| `stone/npi_*_agent/` | 插件式子 Agent | 自动发现，无需改核心代码 |

**向后兼容：** 根目录 `stone/core.py`、`stone/cli.py` 为 shim，旧 import 路径仍可用。

---

通过 `pip install -e .` 安装后在命令行可用：

| 命令 | 模块 | 用途 |
|------|------|------|
| `multi-agent-backend` | `backend.main:app` | 启动 FastAPI / Uvicorn |
| `multi-agent-cli` | `subagent.stone.cli:main` | 命令行直接调 Supervisor（不经 HTTP） |
| `multi-agent-init-demo` | `subagent.config.demo_db:main` | 初始化 / 刷新 `data/demo.db` |

`scripts/demo_db.py` 是上述 init 命令的薄壳，内容等价于 `multi-agent-init-demo`。

---

## 启动入口

| 场景 | 权威命令 |
|------|----------|
| Windows 日常一键启动 | `scripts/run_all.ps1` |
| 分终端开发（跨平台） | `make backend` + `make frontend` |
| 生产 / 已安装 wheel | `multi-agent-backend` |
| 本地 CI 等价检查 | `make ci` |
| 提交前钩子 | `pre-commit run --all-files` |
| **生产部署** | 见 [`docs/DEPLOYMENT.md`](DEPLOYMENT.md) |

---

## 后端分层关键词

| 层 | 职责 |
|----|------|
| `api/v1/` | HTTP 路由 |
| `services/` | 聊天、会话业务编排 |
| `ports/` | 出站能力抽象（如 `AgentService`） |
| `adapters/` | ports 的具体实现（如 `StoneAgentService`） |
| `repositories/` | 数据访问抽象 |
| `infrastructure/` | SQLAlchemy 等基础设施 |
| `app/` | FastAPI factory、DI container、middleware |
| `config/` | 路径、端口、settings（**路径解析一律从 `backend.config.paths` 导入**） |
| `core/` | `ApiResponse`、异常等无业务依赖工具 |

详见 [`src/backend/ARCHITECTURE.md`](../src/backend/ARCHITECTURE.md)。
