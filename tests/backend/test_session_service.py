"""DefaultSessionService unit tests."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from backend.infrastructure.database.engine import create_chat_database
from backend.repositories.sqlalchemy_repository import SqlAlchemySessionRepository
from backend.services.session_service import DefaultSessionService
from subagent.stone.runtime.contracts import StreamEvent, TurnResult


@dataclass
class RecordingAgent:
    cleared: list[str] = field(default_factory=list)

    def invoke(
        self,
        message: str,
        session_id: str | None = None,
        request_id: str | None = None,
    ) -> TurnResult:
        return TurnResult(reply="ok", trace={})

    def stream_events(
        self,
        message: str,
        session_id: str | None = None,
        request_id: str | None = None,
    ):
        yield StreamEvent(type="done", reply="ok", trace={})

    def clear_session_memory(self, session_id: str) -> None:
        self.cleared.append(session_id)


@pytest.fixture
def session_stack(tmp_path):
    database = create_chat_database(tmp_path / "session_service.db")
    repo = SqlAlchemySessionRepository(database)
    repo.init_schema()
    agent = RecordingAgent()
    return DefaultSessionService(repo, agent), agent


def test_create_and_list_sessions(session_stack):
    svc, _agent = session_stack
    created = svc.create_session("标题 A")
    rows = svc.list_sessions()
    assert len(rows) == 1
    assert rows[0]["id"] == created["id"]
    assert rows[0]["title"] == "标题 A"


def test_get_and_update_session(session_stack):
    svc, _agent = session_stack
    created = svc.create_session()
    loaded = svc.get_session(created["id"])
    assert loaded is not None
    assert loaded["messages"] == []

    updated = svc.update_title(created["id"], "新标题")
    assert updated is not None
    assert updated["title"] == "新标题"


def test_delete_session_clears_agent_memory(session_stack):
    svc, agent = session_stack
    created = svc.create_session()
    session_id = created["id"]
    assert svc.ensure_exists(session_id)
    assert svc.delete_session(session_id)
    assert not svc.ensure_exists(session_id)
    assert agent.cleared == [session_id]


def test_update_missing_session_returns_none(session_stack):
    svc, _agent = session_stack
    assert svc.update_title("missing-id", "x") is None


def test_get_missing_session_returns_none(session_stack):
    svc, _agent = session_stack
    assert svc.get_session("missing-id") is None
