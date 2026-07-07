"""Supervisor LLM streaming phase (trace + reply progressive updates)."""

from __future__ import annotations

import json
from collections.abc import Iterator
from langchain_core.messages import HumanMessage
from subagent.config.logging_setup import get_logger
from subagent.config.settings import get_agent_settings
from subagent.stone.routing.classifier import build_supervisor_input
from subagent.stone.runtime.agent_factory import create_supervisor_agent
from subagent.stone.runtime.delta_emitter import ReplyStreamBuffer
from subagent.stone.runtime.fallbacks import api_doc_fallback
from subagent.stone.runtime.streaming.helpers import (
    iter_thinking_growth_events,
    trace_snapshot,
    yield_reply_deltas,
)
from subagent.stone.runtime.subagent_wrapper import (
    begin_nested_trace_capture,
    end_nested_trace_capture,
)
from subagent.stone.runtime.trace import build_thinking_narrative, extract_reply, message_chunk_text
from typing import Any

settings = get_agent_settings()
logger = get_logger("agent.stream.supervisor")


def stream_supervisor_events(
    user_message: str,
    session_id: str | None,
    rid: str,
) -> Iterator[dict[str, Any]]:
    """Yield trace/reply/done events from supervisor agent.stream()."""
    logger.info(
        "[%s] stream start session=%s model=%s",
        rid,
        session_id,
        settings.openai_model,
    )

    agent = create_supervisor_agent()
    config = {"configurable": {"thread_id": session_id}} if session_id else None
    supervisor_input = build_supervisor_input(user_message)
    input_state = {"messages": [HumanMessage(content=supervisor_input)]}

    last_trace_json = ""
    last_reply = ""
    last_thinking_emitted = ""
    final_messages: list[Any] = []
    reply_buffer = ReplyStreamBuffer(chunk_size=settings.reply_buffer_chunk_size)
    chunk = settings.reply_buffer_chunk_size
    got_token_stream = False
    trace: dict[str, Any] = {"agents_used": [], "agent_labels": [], "steps": []}

    yield {"type": "thinking_delta", "delta": "正在分析问题..."}

    trace_bucket = begin_nested_trace_capture()
    try:
        try:
            for item in agent.stream(
                input_state,
                config=config,
                stream_mode=["values", "messages"],
            ):
                mode: str
                data: Any
                if isinstance(item, tuple) and len(item) == 2:
                    mode, data = item
                else:
                    mode, data = "values", item

                if mode == "messages":
                    msg_chunk = data[0] if isinstance(data, tuple) else data
                    delta = message_chunk_text(msg_chunk)
                    if not delta or "redacted_thinking" in delta.lower():
                        continue
                    got_token_stream = True
                    for piece in reply_buffer.feed(delta):
                        yield {"type": "reply_delta", "delta": piece}
                    continue

                if mode != "values" or not isinstance(data, dict):
                    continue

                final_messages = data.get("messages") or final_messages
                trace = trace_snapshot(final_messages)
                narrative = build_thinking_narrative(trace)
                growth_iter, last_thinking_emitted = iter_thinking_growth_events(
                    narrative, last_thinking_emitted, chunk
                )
                yield from growth_iter
                trace_json = json.dumps(trace, ensure_ascii=False, sort_keys=True)
                if trace_json != last_trace_json:
                    last_trace_json = trace_json
                    yield {"type": "trace", "trace": trace}

                reply = extract_reply(final_messages)
                if reply and reply != last_reply:
                    if not got_token_stream:
                        yield from yield_reply_deltas(reply_buffer, reply)
                    else:
                        reply_buffer.feed_growth(reply)
                    last_reply = reply
                    yield {"type": "reply", "reply": reply}

        except Exception as exc:
            logger.error(
                "[%s] stream failed session=%s type=%s err=%s",
                rid,
                session_id,
                type(exc).__name__,
                exc,
            )
            fallback = api_doc_fallback(user_message, exc)
            if fallback is not None:
                yield {"type": "trace", "trace": fallback["trace"]}
                fb_reply = fallback["reply"]
                yield from yield_reply_deltas(reply_buffer, fb_reply)
                last_reply = fb_reply
                yield {"type": "reply", "reply": fb_reply}
                final_messages = []
                trace = fallback["trace"]
            else:
                yield {
                    "type": "error",
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "request_id": rid,
                }
                return
    finally:
        end_nested_trace_capture(trace_bucket)

    if final_messages:
        trace = trace_snapshot(final_messages)
        narrative = build_thinking_narrative(trace)
        growth_iter, last_thinking_emitted = iter_thinking_growth_events(
            narrative, last_thinking_emitted, chunk
        )
        yield from growth_iter
        if last_thinking_emitted:
            yield {"type": "thinking_done"}
        reply = extract_reply(final_messages) or last_reply
        if reply and reply != last_reply:
            yield from yield_reply_deltas(reply_buffer, reply)
        last_reply = reply
        yield {"type": "trace", "trace": trace}
        if reply:
            yield {"type": "reply", "reply": reply}
    else:
        trace = (
            json.loads(last_trace_json)
            if last_trace_json
            else {"agents_used": [], "agent_labels": [], "steps": []}
        )

    if not last_reply and trace.get("steps"):
        for step in reversed(trace.get("steps") or []):
            detail = step.get("detail") or ""
            if detail and len(detail) > 30 and "【API文档】" in detail:
                yield from yield_reply_deltas(reply_buffer, detail)
                last_reply = detail
                yield {"type": "reply", "reply": last_reply}
                break

    logger.info(
        "[%s] stream done session=%s reply_len=%d",
        rid,
        session_id,
        len(last_reply),
    )
    yield {
        "type": "done",
        "success": True,
        "reply": last_reply,
        "trace": trace,
        "request_id": rid,
    }
