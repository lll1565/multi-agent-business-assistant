"""Supervisor-path integration test with fake LLM (no network)."""

from __future__ import annotations

from subagent.stone.routing.resolve_route import RouteKind, resolve_route_kind
from subagent.stone.runtime.core import chat_with_trace


def test_supervisor_route_delegates_to_db_agent(monkeypatch):
    """Ambiguous query → supervisor path; mocked turn returns npi_db_agent trace."""
    message = "对比订单 API 和数据库客户数"
    assert resolve_route_kind(message) == RouteKind.SUPERVISOR

    def fake_supervisor_turn(
        user_message: str,
        session_id: str | None = None,
        request_id: str | None = None,
        routing_hint: str | None = None,
    ) -> dict:
        assert user_message == message
        assert routing_hint is not None
        return {
            "reply": "客户表共 42 行；get_orders 接口返回分页列表。",
            "trace": {
                "agents_used": ["npi_db_agent", "npi_api_agent"],
                "agent_labels": ["数据库", "API 文档"],
                "steps": [
                    {
                        "type": "delegate",
                        "title": "委派数据库 Agent",
                        "detail": "查询客户表行数",
                        "agent": "npi_db_agent",
                    }
                ],
            },
        }

    monkeypatch.setattr(
        "subagent.stone.runtime.entrypoints.run_supervisor_turn",
        fake_supervisor_turn,
    )

    result = chat_with_trace(message, session_id="sess-golden", request_id="req-1")

    assert "npi_db_agent" in result["trace"]["agents_used"]
    assert result["reply"]
    assert "42" in result["reply"]
