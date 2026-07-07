# Multi-Agent System — 目录说明

## 架构

```
用户
  ↓
entrypoints.chat_with_trace   ← 公开入口（core.py 兼容 re-export）
  ↓
resolve_route → fast/hard 或 agent_factory.create_supervisor_agent
  ↓  从 SubAgentRegistry 自动发现
  ├─ hard_route → npi_db_agent     （高置信度数据库问题）
  ├─ fast_path  → npi_api_agent    （高置信度 API 文档问题）
  └─ task 委派 → 子 Agent            （模糊/混合问题）
```

`agent_factory.py` 不再硬编码 subagent 列表 —— 它调用
`registry.discover_stone_agents()` 扫描 `src/subagent/stone/npi_*_agent/`
下所有子包，读取每个包的 `AGENT_SPEC` 常量。

## 目录

```
src/subagent/stone/
├── core.py                 # 兼容 re-export（chat / create_supervisor_agent）
├── agent_factory.py        # Supervisor 工厂（registry → subagents）
├── entrypoints.py          # chat_with_trace / chat / CLI main
├── fallbacks.py            # LLM 失败兜底
├── registry.py             # SubAgentSpec + cancel_when_* + 自动发现
├── routing.py              # 数据驱动分类（读 registry.keywords）
├── hard_route.py           # 确定性硬路由（registry.supports_hard_route=True）
├── api_fastpath.py         # 零 LLM 快路径（registry.supports_fast_path=True）
├── streaming/              # SSE 流式（fast_path / supervisor_phase / helpers）
├── trace.py                # 推理链提取
├── subagent_wrapper.py     # 子 Agent trace + checkpoint
├── checkpointer.py         # LangGraph SQLite 持久化
├── validators.py           # 输入 / SQL 校验
├── prompts.py              # Supervisor / 子 Agent 提示词模板
├── tools/                  # database.py, sql_toolkit.py
├── npi_db_agent/           # 数据库子 Agent（含 AGENT_SPEC）
└── npi_api_agent/          # API 文档子 Agent（含 AGENT_SPEC）
```

## 后端分层

```
backend/
├── api/v1/          # REST + SSE
├── services/        # ChatService, SessionService, StoneAgentService
├── repositories/    # SqliteSessionRepository
└── domain/          # Pydantic 模型
```

## 添加新子 Agent（5 步上手）

> 改一个文件 = 加一个 Agent。

1. **建目录**：`src/subagent/stone/npi_<name>_agent/`
2. **写 `sub_agent.py`**：用 `create_deep_agent` 包一个 `@lru_cache` 工厂函数。
3. **写 `__init__.py`**：导出工厂 + `AGENT_SPEC`（带 `keywords` / `kind` 等）。
4. **写 `AGENTS.md`**：给子 Agent 自己的 LLM 看的工作守则。
5. **加测试**：`tests/test_routing.py` + 工具单测。

`agent_factory` 启动时会自动发现新 Agent，**无需任何修改**。详见 `README.md`
的"如何新增一个子 Agent"章节。