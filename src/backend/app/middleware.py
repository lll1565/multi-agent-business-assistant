"""HTTP middleware."""

import logging
import time
import uuid
from backend.app.rate_limit import get_chat_rate_limiter
from backend.app.security import (
    api_key_is_valid,
    client_ip,
    is_chat_mutation_path,
    is_public_path,
)
from backend.config.logging_setup import get_logger
from backend.config.settings import get_backend_settings
from backend.config.structured_log import log_event, set_request_id
from backend.config.tracing import current_trace_id, span
from backend.core.response import ApiResponse
from collections.abc import Awaitable, Callable
from fastapi import Request
from starlette.responses import JSONResponse, Response

logger = get_logger("backend.api")


async def request_logging_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    req_id = request.headers.get("X-Request-Id") or uuid.uuid4().hex[:10]
    request.state.request_id = req_id
    set_request_id(req_id)
    path = request.url.path
    method = request.method
    t0 = time.perf_counter()

    async def _handle() -> Response:
        log_event(
            logger,
            logging.INFO,
            "http_request_start",
            method=method,
            path=path,
        )
        response = await call_next(request)
        ms = (time.perf_counter() - t0) * 1000
        trace_id = current_trace_id()
        log_event(
            logger,
            logging.INFO,
            "http_request_end",
            method=method,
            path=path,
            status=response.status_code,
            duration_ms=round(ms, 1),
            trace_id=trace_id,
        )
        response.headers["X-Request-Id"] = req_id
        if trace_id:
            response.headers["X-Trace-Id"] = trace_id
        return response

    try:
        with span(
            "http.request",
            attributes={
                "http.method": method,
                "http.route": path,
                "request.id": req_id,
            },
        ):
            return await _handle()
    except Exception:
        ms = (time.perf_counter() - t0) * 1000
        log_event(
            logger,
            logging.ERROR,
            "http_request_failed",
            method=method,
            path=path,
            duration_ms=round(ms, 1),
        )
        logger.exception("[%s] request failed", req_id)
        raise
    finally:
        set_request_id(None)


def _error_response(*, status_code: int, code: int, message: str, request_id: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ApiResponse(
            code=code,
            message=message,
            data=None,
            request_id=request_id,
        ).model_dump(),
    )


async def security_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    settings = get_backend_settings()
    path = request.url.path
    req_id = getattr(request.state, "request_id", None) or "-"

    if settings.api_auth_key and not is_public_path(path):
        if not api_key_is_valid(request, settings.api_auth_key):
            return _error_response(
                status_code=401,
                code=40100,
                message="未授权：缺少或无效的 API Key",
                request_id=req_id,
            )

    if is_chat_mutation_path(path, request.method):
        limiter = get_chat_rate_limiter(settings.chat_rate_limit_per_minute)
        if not limiter.allow(client_ip(request)):
            return _error_response(
                status_code=429,
                code=42900,
                message="请求过于频繁，请稍后再试",
                request_id=req_id,
            )

    return await call_next(request)
