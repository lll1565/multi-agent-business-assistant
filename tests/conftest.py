"""Shared pytest fixtures for API integration tests."""

from __future__ import annotations

import pytest
from backend.app.factory import create_app
from backend.infrastructure.database.engine import create_chat_database, init_schema
from backend.repositories.sqlalchemy_repository import SqlAlchemySessionRepository
from backend.services.chat_service import DefaultChatService
from backend.services.session_service import DefaultSessionService
from dataclasses import dataclass, field
from fastapi.testclient import TestClient
from pathlib import Path
from subagent.stone.runtime.contracts import StreamEvent, TurnResult
from typing import Any


@dataclass
class FakeAgentService:
    """Stub agent — no LLM calls."""

    reply: str = "测试回复"
    trace: dict[str, Any] = field(
        default_factory=lambda: {
            "agents_used": [],
            "agent_labels": [],
            "steps": [],
        }
    )

    def invoke(
        self,
        message: str,
        session_id: str | None = None,
        request_id: str | None = None,
    ) -> TurnResult:
        return TurnResult(reply=self.reply, trace=self.trace)

    def stream_events(
        self,
        message: str,
        session_id: str | None = None,
        request_id: str | None = None,
    ):
        yield StreamEvent(type="started", request_id=request_id or "-")
        yield StreamEvent(type="reply_delta", delta=self.reply)
        yield StreamEvent(
            type="done",
            success=True,
            reply=self.reply,
            trace=self.trace,
            request_id=request_id or "-",
        )

    def clear_session_memory(self, session_id: str) -> None:
        return None


@pytest.fixture
def api_client(tmp_path: Path):
    db_path = tmp_path / "integration_chat.db"
    database = create_chat_database(db_path)
    init_schema(database)
    repo = SqlAlchemySessionRepository(database)
    agent = FakeAgentService()
    container = type(
        "Container",
        (),
        {
            "database": database,
            "session_service": DefaultSessionService(repo, agent),
            "chat_service": DefaultChatService(repo, agent),
        },
    )()

    app = create_app()
    app.state.container = container
    with TestClient(app) as client:
        yield client
