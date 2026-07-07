"""Tests for API doc fast path and LLM-failure rescue."""

from __future__ import annotations

from subagent.stone.routing.api_fastpath import (
    _fast_path_agent,
    clear_fast_path_cache,
    try_api_doc_fast_path,
    try_api_doc_rescue,
)
from subagent.stone.routing.registry import discover_stone_agents
from subagent.stone.runtime.fallbacks import _api_doc_fallback


def test_try_api_doc_rescue_returns_local_doc_for_api_only():
    result = try_api_doc_rescue("get_users 接口文档")
    assert result is not None
    assert result["trace"]["agents_used"] == ["npi_api_agent"]
    assert "get_users" in result["reply"].lower() or "用户" in result["reply"]
    assert "兜底" in result["trace"]["steps"][0]["detail"]


def test_try_api_doc_rescue_list_all_apis():
    result = try_api_doc_rescue("有哪些接口")
    assert result is not None
    assert "get_users" in result["reply"] or "login" in result["reply"]


def test_try_api_doc_rescue_rejects_vague_api_without_endpoint():
    assert try_api_doc_rescue("查看 REST API 文档") is None


def test_try_api_doc_rescue_rejects_db_only():
    assert try_api_doc_rescue("数据库里有哪些表？") is None


def test_try_api_doc_rescue_rejects_mixed_db_and_api():
    assert try_api_doc_rescue("数据库 get_users 和订单表") is None


def test_try_api_doc_rescue_rejects_web_only():
    assert try_api_doc_rescue("联网搜一下 Python 教程") is None


def test_try_api_doc_fast_path_requires_known_target():
    assert try_api_doc_fast_path("查看 REST API 文档") is None


def test_try_api_doc_fast_path_matches_rescue_for_named_api():
    fast = try_api_doc_fast_path("get_users 接口文档")
    rescue = try_api_doc_rescue("get_users 接口文档")
    assert fast is not None and rescue is not None
    assert fast["reply"] == rescue["reply"]


def test_core_api_doc_fallback_delegates_on_connection_error():
    result = _api_doc_fallback("get_users 接口文档", ConnectionError("connection error"))
    assert result is not None
    assert result["trace"]["agents_used"] == ["npi_api_agent"]


def test_core_api_doc_fallback_ignores_non_connection_errors():
    assert _api_doc_fallback("get_users 接口文档", ValueError("bad input")) is None


def test_core_api_doc_fallback_ignores_non_api_queries():
    assert (
        _api_doc_fallback(
            "数据库里有哪些表？",
            ConnectionError("connection error"),
        )
        is None
    )


def test_clear_fast_path_cache_forces_reresolve():
    clear_fast_path_cache()
    discover_stone_agents()
    first = _fast_path_agent()
    second = _fast_path_agent()
    assert first is second

    clear_fast_path_cache()
    third = _fast_path_agent()
    assert third is not None
    assert third.agent_name == first.agent_name


def test_reset_registry_clears_fast_path_cache():
    from subagent.stone.routing.registry import reset_registry

    clear_fast_path_cache()
    discover_stone_agents()
    _fast_path_agent()
    reset_registry()
    assert _fast_path_agent.cache_info().currsize == 0
    discover_stone_agents()


def test_fast_path_logs_import_error(monkeypatch):
    clear_fast_path_cache()

    def _boom(_path):
        raise ImportError("langchain version mismatch")

    monkeypatch.setattr(
        "subagent.stone.routing.api_fastpath.importlib.import_module",
        _boom,
    )
    from subagent.stone.routing.api_fastpath import _resolve_fast_path_agent

    assert _resolve_fast_path_agent() is None
    clear_fast_path_cache()
