"""Unified API response envelope."""

from pydantic import BaseModel, Field
from typing import Generic, TypeVar

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response: {code, message, data, request_id}."""

    code: int = Field(0, description="0 = success; non-zero = business error")
    message: str = "ok"
    data: T | None = None
    request_id: str | None = None


def ok(
    data: T,
    *,
    request_id: str | None = None,
    message: str = "ok",
) -> ApiResponse[T]:
    return ApiResponse(code=0, data=data, request_id=request_id, message=message)
