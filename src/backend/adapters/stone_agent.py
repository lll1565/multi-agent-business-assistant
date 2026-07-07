"""Stone multi-agent adapter  bridges Backend to subagent.stone."""

from __future__ import annotations

import time
import traceback
from backend.config.logging_setup import get_logger
from backend.config.tracing import span
from backend.ports.agent import AgentService
from collections.abc import Iterator
from subagent.stone.runtime.contracts import StreamEvent, TurnResult, normalize_turn_result
from subagent.stone.runtime.trace import build_safe_trace

logger = get_logger("backend.agent")


class StoneAgentService(AgentService):
    """Agent service implemented by subagent.stone."""

    def invoke(self, message: str, session_id: str, request_id: str) -> TurnResult:
        from subagent.stone.runtime.core import chat_with_trace

        logger.info(
            "[%s] agent.invoke start session=%s msg_len=%d preview=%r",
            request_id,
            session_id,
            len(message),
            message[:120],
        )
        t0 = time.perf_counter()
        try:
            with span(
                "agent.invoke",
                attributes={
                    "request.id": request_id,
                    "session.id": session_id,
                    "message.length": len(message),
                },
            ):
                result = chat_with_trace(message, session_id=session_id, request_id=request_id)
            ms = (time.perf_counter() - t0) * 1000
            turn = normalize_turn_result(result)
            agents = turn["trace"].get("agents_used", [])
            turn["trace"] = build_safe_trace(turn["trace"])
            logger.info(
                "[%s] agent.invoke ok session=%s agents=%s reply_len=%d %.0fms",
                request_id,
                session_id,
                agents,
                len(turn["reply"]),
                ms,
            )
            return turn
        except Exception as exc:
            ms = (time.perf_counter() - t0) * 1000
            logger.error(
                "[%s] agent.invoke FAIL session=%s %.0fms type=%s msg=%s",
                request_id,
                session_id,
                ms,
                type(exc).__name__,
                exc,
            )
            logger.debug("[%s] traceback:\n%s", request_id, traceback.format_exc())
            raise

    def stream_events(
        self, message: str, session_id: str, request_id: str
    ) -> Iterator[StreamEvent]:
        from subagent.stone.runtime.streaming import iter_chat_stream_events

        with span(
            "agent.stream",
            attributes={
                "request.id": request_id,
                "session.id": session_id,
                "message.length": len(message),
            },
        ):
            yield from iter_chat_stream_events(message, session_id, request_id)

    def clear_session_memory(self, session_id: str) -> None:
        from subagent.stone.persistence.checkpointer import delete_session_checkpoints

        delete_session_checkpoints(session_id)
