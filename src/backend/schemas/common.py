"""Shared API payload shapes."""

from pydantic import BaseModel
from typing import Any


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
