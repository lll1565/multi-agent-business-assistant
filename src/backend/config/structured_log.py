"""Structured logging helpers —JSON lines + request_id context."""

from __future__ import annotations

import json
import logging
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

from backend.config.tracing import current_trace_id

request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def set_request_id(request_id: str | None) -> None:
    request_id_ctx.set(request_id)


def get_request_id() -> str | None:
    return request_id_ctx.get()


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        rid = get_request_id()
        if rid:
            payload["request_id"] = rid
        trace_id = current_trace_id()
        if trace_id:
            payload["trace_id"] = trace_id
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        for key in ("event", "route", "session_id", "duration_ms", "status", "trace_id"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload, ensure_ascii=False)


def log_event(logger: logging.Logger, level: int, event: str, **fields: Any) -> None:
    extra = {"event": event, **fields}
    logger.log(level, event, extra=extra)
