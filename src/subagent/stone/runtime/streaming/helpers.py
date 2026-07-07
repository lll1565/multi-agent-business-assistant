"""SSE streaming helpers (trace snapshots, thinking/reply deltas)."""

from __future__ import annotations

from collections.abc import Iterator
from subagent.stone.runtime.delta_emitter import ReplyStreamBuffer, iter_uniform_deltas
from subagent.stone.runtime.subagent_wrapper import get_nested_traces
from subagent.stone.runtime.trace import build_trace, merge_nested_traces
from typing import Any


def trace_snapshot(messages: list[Any]) -> dict[str, Any]:
    trace = build_trace(messages)
    return merge_nested_traces(trace, get_nested_traces())


def yield_reply_deltas(buffer: ReplyStreamBuffer, text: str) -> Iterator[dict[str, Any]]:
    for piece in buffer.feed_growth(text):
        yield {"type": "reply_delta", "delta": piece}


def iter_thinking_growth_events(
    narrative: str, last_emitted: str, chunk_size: int
) -> tuple[Iterator[dict[str, Any]], str]:
    """Yield thinking_delta for narrative suffix; return new last_emitted."""
    text = (narrative or "").strip()
    if not text:
        return iter(()), last_emitted
    if text == last_emitted:
        return iter(()), last_emitted
    if text.startswith(last_emitted):
        growth = text[len(last_emitted) :]
    else:
        growth = text

    def _gen() -> Iterator[dict[str, Any]]:
        if not growth:
            return
        for piece in iter_uniform_deltas(growth, chunk_size):
            yield {"type": "thinking_delta", "delta": piece}

    return _gen(), text if growth else last_emitted


def yield_thinking_only(narrative: str, chunk_size: int) -> Iterator[dict[str, Any]]:
    """DeepSeek-style: reasoning first, then thinking_done."""
    text = (narrative or "").strip()
    if not text:
        return
    for piece in iter_uniform_deltas(text, chunk_size):
        yield {"type": "thinking_delta", "delta": piece}
    yield {"type": "thinking_done"}
