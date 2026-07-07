"""Session-related API schemas."""

from backend.schemas.chat import MessageOut
from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    title: str = Field(default="新对话", max_length=80, description="会话标题")


class SessionUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=80, description="新标题")


class SessionOut(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    preview: str | None = None
    messages: list[MessageOut] | None = None
