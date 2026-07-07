"""Chat endpoints - sync and SSE stream."""

from backend.api.deps import get_chat_service, get_request_id, get_session_service
from backend.config.logging_setup import get_logger
from backend.core.exceptions import NotFoundError
from backend.core.response import ApiResponse, ok
from backend.schemas import ChatRequest, ChatResponse
from backend.services.base import ChatService, SessionService
from collections.abc import Iterator
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

router = APIRouter(tags=["聊天"])


def _ensure_session(svc: SessionService, session_id: str, request_id: str) -> None:
    if not svc.ensure_exists(session_id):
        get_logger("backend.api").warning("[%s] chat 404 session=%s", request_id, session_id)
        raise NotFoundError("会话不存在")


@router.post(
    "/sessions/{session_id}/chat",
    response_model=ApiResponse[ChatResponse],
    summary="同步聊天（持久化消息）",
    description="向指定会话发送用户消息，调用 Agent 并返回回复与 trace。",
)
async def session_chat(
    session_id: str,
    body: ChatRequest,
    session_svc: SessionService = Depends(get_session_service),
    chat_svc: ChatService = Depends(get_chat_service),
    request_id: str = Depends(get_request_id),
) -> ApiResponse[ChatResponse]:
    _ensure_session(session_svc, session_id, request_id)
    result = await chat_svc.chat(session_id, body.message.strip(), request_id)
    return ok(result, request_id=request_id)


@router.post(
    "/sessions/{session_id}/chat/stream",
    summary="流式聊天（SSE 推送）",
    description=("Server-Sent Events 流式返回思考过程与回复增量。Content-Type: text/event-stream"),
    responses={
        200: {
            "description": "SSE 事件流",
            "content": {
                "text/event-stream": {
                    "example": 'data: {"type":"reply_delta","delta":"hi"}\n\n',
                }
            },
        }
    },
)
def session_chat_stream(
    session_id: str,
    body: ChatRequest,
    session_svc: SessionService = Depends(get_session_service),
    chat_svc: ChatService = Depends(get_chat_service),
    request_id: str = Depends(get_request_id),
) -> StreamingResponse:
    _ensure_session(session_svc, session_id, request_id)

    def generate() -> Iterator[str]:
        yield from chat_svc.chat_stream(session_id, body.message.strip(), request_id)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Request-Id": request_id,
        },
    )


@router.post(
    "/chat",
    response_model=ApiResponse[ChatResponse],
    summary="无会话聊天（兼容旧接口）",
    description="自动创建会话并发送消息，无需先创建 session。",
)
async def chat_legacy(
    body: ChatRequest,
    chat_svc: ChatService = Depends(get_chat_service),
    request_id: str = Depends(get_request_id),
) -> ApiResponse[ChatResponse]:
    result = await chat_svc.chat_legacy(body.message.strip(), request_id)
    return ok(result, request_id=request_id)
