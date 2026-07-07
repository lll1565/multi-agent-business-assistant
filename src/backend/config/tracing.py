"""Distributed tracing —LangSmith + OpenTelemetry (backend startup)."""

from __future__ import annotations

import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from backend.config.settings import BackendSettings

logger = logging.getLogger("app.tracing")

_tracer: Any | None = None
_otel_configured = False


def configure_tracing(settings: BackendSettings) -> dict[str, bool]:
    langsmith = _configure_langsmith(settings)
    otel = _configure_otel(settings)
    return {"langsmith": langsmith, "otel": otel}


def _configure_langsmith(settings: BackendSettings) -> bool:
    if not settings.langsmith_tracing:
        return False
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    if settings.langsmith_api_key:
        os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
    if settings.langsmith_endpoint:
        os.environ["LANGCHAIN_ENDPOINT"] = settings.langsmith_endpoint
    logger.info("LangSmith tracing enabled project=%s", settings.langsmith_project)
    return True


def _configure_otel(settings: BackendSettings) -> bool:
    global _tracer, _otel_configured
    if not settings.otel_enabled:
        return False
    if _otel_configured:
        return True

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    except ImportError:
        logger.warning("otel_enabled=true but opentelemetry packages not installed")
        return False

    resource = Resource.create({"service.name": settings.otel_service_name})
    provider = TracerProvider(resource=resource)

    if settings.otel_exporter_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,
            )

            exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info("OTEL OTLP exporter endpoint=%s", settings.otel_exporter_endpoint)
        except ImportError:
            logger.warning("OTLP exporter unavailable; falling back to console exporter")
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    else:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        logger.info("OTEL console span exporter enabled (set OTEL_EXPORTER_ENDPOINT for OTLP)")

    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer(settings.otel_service_name)
    _otel_configured = True
    return True


def get_tracer() -> Any | None:
    return _tracer


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
    tracer = get_tracer()
    if tracer is None:
        try:
            from opentelemetry import trace

            tracer = trace.get_tracer("multi-agent-chat")
            provider = trace.get_tracer_provider()
            if provider.__class__.__name__ == "ProxyTracerProvider":
                yield None
                return
        except ImportError:
            yield None
            return

    with tracer.start_as_current_span(name) as otel_span:
        for key, value in (attributes or {}).items():
            if value is not None:
                otel_span.set_attribute(key, value)
        yield otel_span


def shutdown_tracing() -> None:
    global _otel_configured
    if not _otel_configured:
        return
    try:
        from opentelemetry import trace

        provider = trace.get_tracer_provider()
        shutdown = getattr(provider, "shutdown", None)
        if callable(shutdown):
            shutdown()
            logger.info("OTEL tracer provider shut down")
    except ImportError:
        pass
    finally:
        _otel_configured = False
