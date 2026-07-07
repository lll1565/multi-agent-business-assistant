"""Stream chat events for SSE (trace + reply progressive updates)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from subagent.config.logging_setup import get_logger
from subagent.stone.routing.resolve_route import RouteKind, resolve_route
from subagent.stone.runtime.streaming.fast_path import emit_fast_or_hard_result
from subagent.stone.runtime.streaming.supervisor_phase import stream_supervisor_events

logger = get_logger("agent.stream")


def iter_chat_stream_events(
    user_message: str,
    session_id: str | None = None,
    request_id: str | None = None,
) -> Iterator[dict[str, Any]]:
    """Yield stream events: started, trace, reply_delta, reply, done, error."""
    rid = request_id or "-"
    decision = resolve_route(
        user_message,
        session_id=session_id,
        request_id=rid,
    )

    if decision.kind == RouteKind.INVALID:
        yield {
            "type": "error",
            "error": decision.validation_error,
            "error_type": "ValidationError",
        }
        return

    yield {"type": "started", "request_id": rid}

    if decision.result is not None:
        logger.info(
            "[%s] stream fast/hard route=%s session=%s",
            rid,
            decision.kind.value,
            session_id,
        )
        yield from emit_fast_or_hard_result(decision.result, rid)
        return

    yield from stream_supervisor_events(user_message, session_id, rid)


__all__ = ["iter_chat_stream_events"]
