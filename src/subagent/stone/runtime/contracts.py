"""Stable contracts between Agent capability layer and Backend adapter."""

from __future__ import annotations

from typing import Any, TypedDict


class AgentTrace(TypedDict, total=False):
    """Reasoning trace returned by one agent turn."""

    agents_used: list[str]
    agent_labels: list[str]
    steps: list[dict[str, Any]]


class TurnResult(TypedDict):
    """Synchronous agent turn result."""

    reply: str
    trace: AgentTrace


class StreamEvent(TypedDict, total=False):
    """One SSE/stream event emitted during agent execution."""

    type: str
    reply: str
    trace: AgentTrace
    delta: str
    error: str
    error_type: str
    success: bool
    request_id: str


def normalize_turn_result(raw: dict[str, Any]) -> TurnResult:
    """Coerce agent output into the stable TurnResult contract."""
    trace_raw = raw.get("trace")
    trace: AgentTrace
    if isinstance(trace_raw, dict):
        trace = trace_raw  # type: ignore[assignment]
    else:
        trace = {"agents_used": [], "agent_labels": [], "steps": []}
    return TurnResult(reply=str(raw.get("reply", "")), trace=trace)
