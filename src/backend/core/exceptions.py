"""Application exceptions and FastAPI handlers."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.core.response import ApiResponse


class AppError(Exception):
    """Raised for expected business failures with stable error codes."""

    def __init__(
        self,
        message: str,
        *,
        code: int = 50000,
        status_code: int = 500,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, message: str = "会话不存在", *, code: int = 40401) -> None:
        super().__init__(message, code=code, status_code=404)


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _error_body(
    *,
    code: int,
    message: str,
    request_id: str | None,
) -> dict[str, Any]:
    return ApiResponse(
        code=code,
        message=message,
        data=None,
        request_id=request_id,
    ).model_dump()


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(
                code=exc.code,
                message=exc.message,
                request_id=_request_id(request),
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, list):
            message = "请求参数错误"
        elif isinstance(detail, dict):
            message = str(detail.get("message") or detail)
        else:
            message = str(detail)
        code = exc.status_code * 100
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(
                code=code,
                message=message,
                request_id=_request_id(request),
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_error_body(
                code=42200,
                message="请求参数校验失败",
                request_id=_request_id(request),
            ),
        )
