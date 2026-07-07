"""DefaultChatService unit tests."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import pytest

from backend.infrastructure.database.engine import create_chat_database
from backend.repositories.sqlalchemy_repository import SqlAlchemySessionRepository
from backend.services.chat_service import DefaultChatService
from subagent.stone.runtime.contracts import StreamEvent, TurnResult


@dataclass
class StubAgent:
    reply: str = "助手回复"
    trace: dict[str, Any] = field(
        default_factory=lambda: {
            "agents_used": ["npi_db_agent"],
            "agent_labels": ["数据库"],
            "steps": [],
        }
    )
    fail: bool = False
    stream_error: str | None = None

    def invoke(
        self,
        message: str,
        session_id: str | None = None,
        request_id: str | None = None,
    ) -> TurnResult:
        if self.fail:
            raise RuntimeError("LLM 失败")
        return TurnResult(reply=self.reply, trace=self.trace)

    def stream_events(
        self,
        message: str,
        session_id: str | None = None,
        request_id: str | None = None,
    ):
        if self.stream_error:
            yield StreamEvent(type="error", error=self.stream_error)
            return
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
def chat_stack(tmp_path):
    database = create_chat_database(tmp_path / "chat_service.db")
    repo = SqlAlchemySessionRepository(database)
    repo.init_schema()
    session = repo.create_session()
    agent = StubAgent()
    svc = DefaultChatService(repo, agent)
    return svc, repo, session.id, agent


@pytest.mark.asyncio
async def test_chat_success_persists_messages(chat_stack):
    svc, repo, session_id, _agent = chat_stack
    result = await svc.chat(session_id, "你好", "req-1")
    assert result.success is True
    assert result.reply == "助手回复"
    assert result.request_id == "req-1"
    loaded = repo.get_session(session_id)
    assert loaded is not None
    assert len(loaded.messages) == 2
    assert loaded.messages[0].role == "user"
    assert loaded.messages[0].content == "你好"
    assert loaded.messages[1].role == "assistant"
    assert loaded.messages[1].content == "助手回复"


@pytest.mark.asyncio
async def test_chat_failure_records_error_message(chat_stack):
    svc, repo, session_id, agent = chat_stack
    agent.fail = True
    result = await svc.chat(session_id, "触发错误", "req-2")
    assert result.success is False
    assert result.error_type == "RuntimeError"
    loaded = repo.get_session(session_id)
    assert loaded is not None
    assert loaded.messages[-1].content.startswith("（生成失败：")


def test_chat_stream_emits_sse_and_persists(chat_stack):
    svc, repo, session_id, _agent = chat_stack
    lines = list(svc.chat_stream(session_id, "流式问题", "req-3"))
    assert lines
    payload = json.loads(lines[-1].removeprefix("data: ").strip())
    assert payload["type"] == "done"
    loaded = repo.get_session(session_id)
    assert loaded is not None
    assert any(m.role == "assistant" and m.content == "助手回复" for m in loaded.messages)


def test_chat_stream_error_event_persists_failure(chat_stack):
    svc, repo, session_id, agent = chat_stack
    agent.stream_error = "流式失败"
    lines = list(svc.chat_stream(session_id, "bad", "req-4"))
    assert any('"type": "error"' in line for line in lines)
    loaded = repo.get_session(session_id)
    assert loaded is not None
    assert loaded.messages[-1].content.startswith("（生成失败：")


@pytest.mark.asyncio
async def test_chat_legacy_creates_session(chat_stack):
    svc, _repo, _session_id, _agent = chat_stack
    result = await svc.chat_legacy("legacy 问题", "req-5")
    assert result.success is True
    assert result.reply == "助手回复"
