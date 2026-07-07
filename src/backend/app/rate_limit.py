"""In-memory sliding-window rate limiter for chat endpoints."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock


class SlidingWindowRateLimiter:
    """Per-key request cap within a fixed time window."""

    def __init__(self, limit: int, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        if self.limit <= 0:
            return True
        now = time.monotonic()
        with self._lock:
            bucket = self._hits[key]
            while bucket and now - bucket[0] > self.window_seconds:
                bucket.popleft()
            if len(bucket) >= self.limit:
                return False
            bucket.append(now)
            return True


_limiter: SlidingWindowRateLimiter | None = None
_limiter_limit = -1


def get_chat_rate_limiter(limit_per_minute: int) -> SlidingWindowRateLimiter:
    global _limiter, _limiter_limit
    if _limiter is None or _limiter_limit != limit_per_minute:
        _limiter = SlidingWindowRateLimiter(limit_per_minute)
        _limiter_limit = limit_per_minute
    return _limiter


def reset_chat_rate_limiter() -> None:
    """Test helper — drop cached limiter."""
    global _limiter, _limiter_limit
    _limiter = None
    _limiter_limit = -1
