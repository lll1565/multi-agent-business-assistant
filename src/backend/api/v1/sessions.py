"""Session CRUD endpoints."""

from backend.api.deps import get_request_id, get_session_service
from backend.core.exceptions import NotFoundError
from backend.core.response import ApiResponse, ok
from backend.schemas import OkData, SessionCreate, SessionListData, SessionUpdate
from backend.services.base import SessionService
from fastapi import APIRouter, Depends
from typing import Any

router = APIRouter(prefix="/sessions", tags=["会话"])


@router.get(
    "",
    response_model=ApiResponse[SessionListData],
    summary="列出会话",
    description="返回所有会话摘要（标题、预览、更新时间）。",
)
def list_sessions(
    svc: SessionService = Depends(get_session_service),
    request_id: str = Depends(get_request_id),
) -> ApiResponse[SessionListData]:
    return ok(SessionListData(sessions=svc.list_sessions()), request_id=request_id)


@router.post(
    "",
    summary="创建会话",
    description="创建空会话，可选标题。",
)
def create_session(
    svc: SessionService = Depends(get_session_service),
    request_id: str = Depends(get_request_id),
    body: SessionCreate | None = None,
) -> ApiResponse[Any]:
    title = (body.title if body else None) or "新对话"
    return ok(svc.create_session(title=title), request_id=request_id)


@router.get(
    "/{session_id}",
    summary="获取会话详情",
    description="返回会话元数据与消息列表（含 trace）。",
)
def get_session(
    session_id: str,
    svc: SessionService = Depends(get_session_service),
    request_id: str = Depends(get_request_id),
) -> ApiResponse[Any]:
    session = svc.get_session(session_id)
    if not session:
        raise NotFoundError("会话不存在")
    return ok(session, request_id=request_id)


@router.patch(
    "/{session_id}",
    summary="更新会话标题",
)
def update_session(
    session_id: str,
    body: SessionUpdate,
    svc: SessionService = Depends(get_session_service),
    request_id: str = Depends(get_request_id),
) -> ApiResponse[Any]:
    session = svc.update_title(session_id, body.title)
    if not session:
        raise NotFoundError("会话不存在")
    return ok(session, request_id=request_id)


@router.delete(
    "/{session_id}",
    response_model=ApiResponse[OkData],
    summary="删除会话",
    description="删除会话及其消息，并清理 Agent checkpoint 缓存。",
)
def delete_session(
    session_id: str,
    svc: SessionService = Depends(get_session_service),
    request_id: str = Depends(get_request_id),
) -> ApiResponse[OkData]:
    if not svc.delete_session(session_id):
        raise NotFoundError("会话不存在")
    return ok(OkData(ok=True), request_id=request_id)
