"""Tests for uniform SSE delta emission."""

from subagent.stone.runtime.delta_emitter import (
    ReplyStreamBuffer,
    iter_growth_deltas,
    iter_uniform_deltas,
)


def test_iter_uniform_deltas_single_chars():
    assert list(iter_uniform_deltas("abc", 1)) == ["a", "b", "c"]


def test_iter_growth_deltas_suffix_only():
    assert list(iter_growth_deltas("hel", "hello", 1)) == ["l", "o"]


def test_reply_stream_buffer_feed_growth():
    buf = ReplyStreamBuffer(chunk_size=1)
    d1 = buf.feed_growth("你好")
    d2 = buf.feed_growth("你好世界")
    assert d1 == ["你", "好"]
    assert d2 == ["世", "界"]
    assert buf.emitted == "你好世界"
