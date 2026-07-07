"""Tests for dynamic capability catalog from SubAgent registry."""

from subagent.stone.routing.capability_catalog import (
    build_capability_reply,
    build_greeting_reply,
    resolve_capability_title,
)
from subagent.stone.routing.meta_fastpath import build_meta_reply, try_meta_fast_path
from subagent.stone.routing.registry import SubAgentSpec, discover_stone_agents, reset_registry


def _dummy_factory():
    class _Noop:
        def invoke(self, *args, **kwargs):
            return {"messages": []}

    return _Noop()


def test_capability_reply_lists_all_registered_agents():
    reset_registry()
    try:
        reply = build_capability_reply()
        assert "4 类能力" in reply
        assert "### 数据库查询" in reply
        assert "### API 接口文档" in reply
        assert "### 网页搜索" in reply
        assert "### 图表绘制" in reply
        assert "系统工作流程" in reply
        assert "get_users 接口文档" in reply
        assert "画一个下单流程图" in reply
    finally:
        reset_registry()


def test_greeting_reply_mentions_all_capabilities():
    reset_registry()
    try:
        reply = build_greeting_reply()
        assert "数据库查询" in reply
        assert "API 接口文档" in reply
        assert "网页搜索" in reply
        assert "图表绘制" in reply
    finally:
        reset_registry()


def test_meta_fast_path_capability_query():
    reset_registry()
    try:
        result = try_meta_fast_path("你能做什么？")
        assert result is not None
        assert "网页搜索" in result["reply"]
        assert "图表绘制" in result["reply"]
        assert result["trace"]["agents_used"] == []
    finally:
        reset_registry()


def test_meta_fast_path_system_workflow_query():
    reset_registry()
    try:
        result = try_meta_fast_path("介绍系统工作流程")
        assert result is not None
        reply = result["reply"]
        assert "数据库查询" in reply
        assert "API 接口文档" in reply
        assert "网页搜索" in reply
        assert "图表绘制" in reply
        assert "系统工作流程" in reply
        assert "npi_" not in reply
        assert "Supervisor" not in reply
        assert "委派" not in reply
    finally:
        reset_registry()


def test_real_diagram_request_is_not_meta_fast_path():
    assert try_meta_fast_path("帮我画一个业务流程图") is None


def test_new_agent_extends_capability_reply():
    reset_registry()
    try:
        discover_stone_agents()
        from subagent.stone.routing.registry import get_registry

        get_registry().register(
            SubAgentSpec(
                name="npi_demo_agent",
                description="演示扩展能力。",
                factory=_dummy_factory,
                kind="demo",
                capability_title="演示扩展",
                capability_bullets=("新增 Agent 后自动出现在帮助里",),
                capability_examples=("试一下演示能力",),
                capability_order=5,
            )
        )
        reply = build_meta_reply("help")
        assert "### 演示扩展" in reply
        assert "5 类能力" in reply
        assert "试一下演示能力" in reply
    finally:
        reset_registry()


def test_resolve_capability_title_fallback():
    spec = SubAgentSpec(
        name="npi_x",
        description="x",
        factory=_dummy_factory,
        kind="web",
    )
    assert resolve_capability_title(spec) == "网页搜索"
