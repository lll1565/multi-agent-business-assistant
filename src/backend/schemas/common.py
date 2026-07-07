"""Shared API payload shapes."""

from typing import Any

from pydantic import BaseModel


class OkResponse(BaseModel):
    ok: bool = True


class OkData(BaseModel):
    ok: bool = True


class SessionListData(BaseModel):
    sessions: list[dict[str, Any]]


class RootData(BaseModel):
    message: str
    docs: str = "/api/docs"
    health: str = "/api/health"
