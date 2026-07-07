"""Lightweight tracing helpers for agent code (uses global OTEL provider if configured)."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any


def current_trace_id() -> str | None:
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        ctx = span.get_span_context()
        if ctx.is_valid:
            return format(ctx.trace_id, "032x")
    except ImportError:
        pass
    return None


@contextmanager
def span(
    name: str,
    *,
    attributes: dict[str, Any] | None = None,
) -> Iterator[Any | None]:
    try:
        from opentelemetry import trace
        from opentelemetry.trace import NoOpTracerProvider

        provider = trace.get_tracer_provider()
        if isinstance(provider, NoOpTracerProvider):
            yield None
            return

        tracer = trace.get_tracer("multi-agent-chat")
        with tracer.start_as_current_span(name) as otel_span:
            for key, value in (attributes or {}).items():
                if value is not None:
                    otel_span.set_attribute(key, value)
            yield otel_span
    except ImportError:
        yield None
