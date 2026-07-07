"""Tests for the npi_diagram_agent (routing + tool formatting + fallback)."""

from pathlib import Path

import pytest

from subagent.stone.npi_diagram_agent.tools import (
    _format_size,
    _resolve_dot_binary,
    _safe_filename,
    render_diagram,
)
from subagent.stone.routing.classifier import (
    classify_query,
    classify_query_agents,
    get_routing_hint,
)
from subagent.stone.routing.registry import discover_stone_agents, get_registry


def test_discover_finds_diagram_agent():
    discover_stone_agents()
    spec = get_registry().get("npi_diagram_agent")
    assert spec is not None
    assert spec.kind == "diagram"
    assert spec.exclusive_keywords
    assert spec.exclusive_cancel_keywords


def test_diagram_agent_build_is_cached(monkeypatch):
    from subagent.stone.npi_diagram_agent import sub_agent as diagram_sub_agent

    sentinel = object()
    build_count = 0

    def fake_create_llm():
        return object()

    def fake_create_deep_agent(**_kwargs):
        nonlocal build_count
        build_count += 1
        return sentinel

    monkeypatch.setattr(diagram_sub_agent, "_create_llm", fake_create_llm)
    monkeypatch.setattr(
        diagram_sub_agent,
        "create_deep_agent",
        fake_create_deep_agent,
    )

    diagram_sub_agent.create_npi_diagram_agent.cache_clear()
    try:
        a1 = diagram_sub_agent.create_npi_diagram_agent()
        a2 = diagram_sub_agent.create_npi_diagram_agent()

        assert a1 is a2
        assert a1 is sentinel
        assert build_count == 1
    finally:
        diagram_sub_agent.create_npi_diagram_agent.cache_clear()


@pytest.mark.parametrize(
    "message",
    [
        "画一个 CPU 架构图",
        "画一张流程图",
        "帮我画个时序图",
        "做个架构图",
        "draw a flowchart",
        "render the dependency graph",
    ],
)
def test_classify_query_agents_routes_to_diagram(message: str):
    agents = classify_query_agents(message)
    assert "npi_diagram_agent" in agents, f"expected diagram agent for {message!r}, got {agents}"


def test_legacy_classify_returns_none_for_diagram_query():
    assert classify_query("画一个流程图") is None


def test_db_query_not_rerouted_to_diagram():
    agents = classify_query_agents("数据库里有哪些表？")
    assert "npi_db_agent" in agents
    assert "npi_diagram_agent" not in agents


def test_routing_hint_names_diagram_agent():
    hint = get_routing_hint("画一个架构图")
    assert hint is not None
    assert "npi_diagram_agent" in hint


def test_safe_filename_strips_unsafe():
    assert _safe_filename("Hello/World:Test?.png") == "Hello_World_Test_.png"
    assert _safe_filename("") == "diagram"
    assert _safe_filename("...") == "diagram"


def test_safe_filename_truncates():
    long = "a" * 200
    assert len(_safe_filename(long)) <= 64


def test_format_size():
    assert _format_size(512) == "512 B"
    assert _format_size(2048).endswith("KB")
    assert _format_size(2 * 1024 * 1024).endswith("MB")


def test_render_diagram_rejects_empty_code():
    out = render_diagram.invoke({"dot_code": ""})
    assert "不能为空" in out


def test_render_diagram_rejects_invalid_format():
    out = render_diagram.invoke({"dot_code": "digraph G { a }", "output_format": "bmp"})
    assert "不支持的格式" in out


def test_render_diagram_rejects_invalid_engine():
    out = render_diagram.invoke({"dot_code": "digraph G { a }", "engine": "magic"})
    assert "不支持的 engine" in out


def test_render_diagram_dot_format_returns_source_only():
    out = render_diagram.invoke({"dot_code": "digraph G { A -> B }", "output_format": "dot"})
    assert "```dot" in out
    assert "A -> B" in out
    assert "![" not in out


def test_render_diagram_falls_back_to_dot_source_when_no_binary(monkeypatch):
    monkeypatch.setattr(
        "subagent.stone.npi_diagram_agent.tools._resolve_dot_binary",
        lambda: None,
    )
    out = render_diagram.invoke(
        {"dot_code": "digraph G { X -> Y }", "output_name": "fallback_test"}
    )
    assert "已返回 DOT 源码" in out
    assert "```dot" in out
    assert "X -> Y" in out
    assert "GRAPHVIZ_BIN" in out or "graphviz.org" in out


def test_render_diagram_with_no_graphviz_includes_install_hint(monkeypatch):
    monkeypatch.setattr(
        "subagent.stone.npi_diagram_agent.tools._resolve_dot_binary",
        lambda: None,
    )
    out = render_diagram.invoke({"dot_code": "digraph G { a }", "output_name": "hint_test"})
    assert "graphviz" in out.lower()


def test_resolve_dot_binary_returns_string_or_none():
    result = _resolve_dot_binary()
    assert result is None or isinstance(result, str)
    if result is not None:
        assert Path(result).is_file()


def test_resolve_dot_binary_respects_env_var(monkeypatch):
    fake = Path("data") / "diagrams" / "_test_fake_dot.exe"
    fake.parent.mkdir(parents=True, exist_ok=True)
    try:
        fake.write_text("")
        monkeypatch.setenv("GRAPHVIZ_BIN", str(fake))
        monkeypatch.delenv("GRAPHVIZ_BIN_DIR", raising=False)
        assert _resolve_dot_binary() == str(fake.resolve())
    finally:
        try:
            fake.unlink()
        except FileNotFoundError:
            pass
