"""Supervisor turn execution ? shared by sync and streaming paths."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage

from subagent.config.logging_setup import get_logger
from subagent.config.settings import get_agent_settings
from subagent.config.tracing import span
from subagent.stone.routing.classifier import build_supervisor_input
from subagent.stone.runtime.agent_factory import create_supervisor_agent
from subagent.stone.runtime.contracts import TurnResult, normalize_turn_result
from subagent.stone.runtime.fallbacks import _api_doc_fallback, _fallback_reply
from subagent.stone.runtime.subagent_wrapper import (
    begin_nested_trace_capture,
    end_nested_trace_capture,
)
from subagent.stone.runtime.trace import build_trace, extract_reply, merge_nested_traces

settings = get_agent_settings()
logger = get_logger("agent.turn_runner")


def run_supervisor_turn(
    user_message: str,
    session_id: str | None = None,
    request_id: str | None = None,
    routing_hint: str | None = None,
) -> TurnResult:
    """Invoke the supervisor after fast/hard paths did not apply."""
    rid = request_id or "-"
    logger.info(
        "[%s] supervisor turn session=%s model=%s base_url=%s routing=%r",
        rid,
        session_id,
        settings.openai_model,
        settings.openai_base_url,
        routing_hint,
    )

    agent = create_supervisor_agent()
    invoke_kwargs: dict[str, Any] = {}
    if session_id:
        invoke_kwargs["config"] = {"configurable": {"thread_id": session_id}}

    supervisor_input = build_supervisor_input(user_message)
    trace_bucket = begin_nested_trace_capture()
    try:
        with span(
            "agent.supervisor_turn",
            attributes={
                "request.id": rid,
                "session.id": session_id or "",
                "llm.model": settings.openai_model,
            },
        ):
            try:
                result = agent.invoke(
                    {"messages": [HumanMessage(content=supervisor_input)]},
                    **invoke_kwargs,
                )
            except Exception as exc:
                logger.error(
                    "[%s] supervisor invoke failed session=%s type=%s err=%s",
                    rid,
                    session_id,
                    type(exc).__name__,
                    exc,
                )
                fallback = _api_doc_fallback(user_message, exc)
                if fallback is not None:
                    logger.warning(
                        "[%s] using API doc fallback session=%s reason=%s",
                        rid,
                        session_id,
                        exc,
                    )
                    return normalize_turn_result(fallback)
                raise
    finally:
        nested_traces = end_nested_trace_capture(trace_bucket)

    messages = result.get("messages", [])
    trace = build_trace(messages)
    trace = merge_nested_traces(trace, nested_traces)
    reply = extract_reply(messages)
    if not reply:
        reply = _fallback_reply(messages)
    logger.info(
        "[%s] supervisor done session=%s agents=%s steps=%d reply_len=%d",
        rid,
        session_id,
        trace.get("agents_used"),
        len(trace.get("steps") or []),
        len(reply),
    )
    return TurnResult(reply=reply, trace=trace)


__all__ = ["run_supervisor_turn"]
