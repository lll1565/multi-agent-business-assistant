"""SSE emission for fast-path / hard-route results."""

from __future__ import annotations

from collections.abc import Iterator
from subagent.config.settings import get_agent_settings
from subagent.stone.runtime.delta_emitter import ReplyStreamBuffer, iter_uniform_deltas
from subagent.stone.runtime.streaming.helpers import yield_thinking_only
from subagent.stone.runtime.trace import build_thinking_narrative
from typing import Any

settings = get_agent_settings()


def emit_fast_or_hard_result(result: dict[str, Any], rid: str) -> Iterator[dict[str, Any]]:
    """Emit SSE events for fast-path / hard-route results with uniform deltas."""
    reply = result["reply"]
    trace = result["trace"]
    chunk = settings.reply_buffer_chunk_size
    buffer = ReplyStreamBuffer(chunk_size=chunk)
    yield {"type": "thinking_delta", "delta": "正在分析问题..."}
    yield from yield_thinking_only(build_thinking_narrative(trace), chunk)
    yield {"type": "trace", "trace": trace}
    for piece in iter_uniform_deltas(reply, chunk):
        yield {"type": "reply_delta", "delta": piece}
    buffer.feed_growth(reply)
    yield {"type": "reply", "reply": reply}
    yield {
        "type": "done",
        "success": True,
        "reply": reply,
        "trace": trace,
        "request_id": rid,
    }
