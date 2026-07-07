"""Health check API schemas."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "multi-agent-chat"
    model: str | None = None
    log_file: str | None = None
    docs_url: str = "/api/docs"


class ReadyCheck(BaseModel):
    name: str
    ok: bool
    detail: str | None = None


class ReadyResponse(BaseModel):
    status: str
    checks: list[ReadyCheck]
