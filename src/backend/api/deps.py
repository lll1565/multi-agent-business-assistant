"""FastAPI dependencies - resolve services from container."""

from backend.app.container import AppContainer
from backend.services.base import ChatService, SessionService
from fastapi import Request
from typing import cast


def get_container(request: Request) -> AppContainer:
    return cast(AppContainer, request.app.state.container)


def get_session_service(request: Request) -> SessionService:
    return get_container(request).session_service


def get_chat_service(request: Request) -> ChatService:
    return get_container(request).chat_service


def get_request_id(request: Request) -> str:
    import uuid

    return getattr(request.state, "request_id", uuid.uuid4().hex[:10])
