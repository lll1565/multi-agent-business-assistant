"""Uniform character-level delta emission —decouples LLM chunks from SSE display."""

from __future__ import annotations

from collections.abc import Iterator


def iter_uniform_deltas(text: str, chunk_size: int = 1) -> Iterator[str]:
    """Yield text in fixed-size slices for steady frontend rendering."""
    if not text or chunk_size < 1:
        return
    for i in range(0, len(text), chunk_size):
        yield text[i : i + chunk_size]


def iter_growth_deltas(old: str, new: str, chunk_size: int = 1) -> Iterator[str]:
    """Emit only the suffix when reply grows; re-emit full text on replacement."""
    if not new or new == old:
        return
    if new.startswith(old):
        yield from iter_uniform_deltas(new[len(old) :], chunk_size)
        return
    yield from iter_uniform_deltas(new, chunk_size)


class ReplyStreamBuffer:
    """Track emitted reply length to avoid duplicate SSE deltas."""

    def __init__(self, chunk_size: int = 1) -> None:
        self.chunk_size = chunk_size
        self._emitted = ""

    @property
    def emitted(self) -> str:
        return self._emitted

    def feed(self, text: str) -> list[str]:
        """Append streaming chunk; return new uniform deltas only."""
        if not text:
            return []
        if text.startswith(self._emitted) and len(text) > len(self._emitted):
            suffix = text[len(self._emitted) :]
        elif self._emitted and text in self._emitted:
            return []
        else:
            suffix = text
            self._emitted = ""
        deltas = list(iter_uniform_deltas(suffix, self.chunk_size))
        self._emitted += suffix
        return deltas

    def feed_growth(self, new_full: str) -> list[str]:
        """Emit deltas for reply growth (values-mode snapshot updates)."""
        deltas = list(iter_growth_deltas(self._emitted, new_full, self.chunk_size))
        if new_full:
            self._emitted = new_full
        return deltas
