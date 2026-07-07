"""Chat-related API schemas."""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="用户消息",
        examples=["查 get_users 接口文档", "数据库里有哪些表？"],
    )

    @field_validator("message")
    @classmethod
    def strip_and_reject_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("消息不能为空")
        return stripped


class ReasoningStep(BaseModel):
    type: str = Field(description="步骤类型：thinking / delegate / tool_result 等")
    title: str
    detail: str | None = None
    agent: str | None = None


class ReasoningTrace(BaseModel):
    agents_used: list[str] = Field(default_factory=list)
    agent_labels: list[str] = Field(default_factory=list)
    steps: list[ReasoningStep] = Field(default_factory=list)


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    created_at: str
    trace: ReasoningTrace | dict[str, Any] | None = None


class ChatResponse(BaseModel):
    reply: str = Field(description="助手回复正文")
    success: bool = True
    error: str | None = None
    error_type: str | None = None
    request_id: str | None = None
    trace: ReasoningTrace | None = None
    user_message: dict[str, Any] | None = None
    assistant_message: dict[str, Any] | None = None
