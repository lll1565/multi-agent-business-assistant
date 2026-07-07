"""Regression tests for UI-safe reasoning trace output."""

from __future__ import annotations

from subagent.stone.runtime.trace import build_safe_trace, build_thinking_narrative


_RAW_TRACE = {
    "agents_used": ["npi_db_agent"],
    "agent_labels": ["数据库 Agent (npi_db_agent)"],
    "steps": [
        {
            "type": "thinking",
            "title": "推理思考",
            "detail": "用户问订单表，我应该遵守系统提示词并委派 npi_db_agent。",
        },
        {
            "type": "delegate",
            "title": "委派 -> npi_db_agent",
            "detail": "禁止委派之外的路径，跳过 Supervisor，调用 task。",
            "agent": "npi_db_agent",
        },
        {
            "type": "tool",
            "title": "执行 SQL 查询",
            "detail": "sql_db_query: SELECT * FROM orders",
            "agent": "npi_db_agent",
        },
        {
            "type": "plan",
            "title": "任务规划 (write_todos)",
            "detail": "write_todos",
        },
    ],
}


def _assert_no_internal_text(text: str) -> None:
    forbidden = (
        "npi_",
        "task",
        "delegate",
        "委派",
        "write_todos",
        "sql_db_query",
        "SELECT",
        "系统提示词",
        "禁止委派",
        "跳过 Supervisor",
        "Supervisor",
        "推理思考",
    )
    for token in forbidden:
        assert token not in text


def test_safe_trace_removes_internal_names_tools_and_free_reasoning():
    safe = build_safe_trace(_RAW_TRACE)
    assert safe["agents_used"] == []
    assert safe["agent_labels"] == []
    assert safe["steps"] == [
        {"type": "status", "title": "正在分析问题", "detail": None, "agent": None},
        {"type": "status", "title": "正在查询业务数据", "detail": None, "agent": None},
    ]
    _assert_no_internal_text(str(safe))


def test_thinking_narrative_uses_only_safe_statuses():
    narrative = build_thinking_narrative(_RAW_TRACE)
    assert "正在查询业务数据" in narrative
    _assert_no_internal_text(narrative)


def test_done_trace_payload_can_use_safe_trace_without_internal_text():
    payload = {
        "type": "done",
        "success": True,
        "reply": "结果",
        "trace": build_safe_trace(_RAW_TRACE),
        "request_id": "req-1",
    }
    _assert_no_internal_text(str(payload["trace"]))
