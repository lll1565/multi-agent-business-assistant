"""SessionRepository SQLAlchemy 实现测试。"""

import pytest

from backend.infrastructure.database.engine import create_chat_database
from backend.repositories.sqlalchemy_repository import SqlAlchemySessionRepository


@pytest.fixture
def repo(tmp_path):
    db_path = tmp_path / "test_chat.db"
    database = create_chat_database(db_path)
    repository = SqlAlchemySessionRepository(database)
    repository.init_schema()
    return repository


def test_create_and_get_session(repo):
    session = repo.create_session("测试会话")
    loaded = repo.get_session(session.id)
    assert loaded is not None
    assert loaded.title == "测试会话"
    assert loaded.messages == []


def test_add_message_with_trace(repo):
    session = repo.create_session()
    msg = repo.add_message(
        session.id,
        "assistant",
        "hello",
        trace={"agents_used": ["npi_db_agent"], "steps": []},
    )
    assert msg.trace["agents_used"] == ["npi_db_agent"]
    loaded = repo.get_session(session.id)
    assert len(loaded.messages) == 1
    assert loaded.messages[0].content == "hello"


def test_list_sessions_preview(repo):
    session = repo.create_session()
    repo.add_message(session.id, "user", "第一条用户消息")
    rows = repo.list_sessions()
    assert rows[0].preview == "第一条用户消息"


def test_auto_title(repo):
    session = repo.create_session()
    repo.auto_title_from_message(session.id, "这是一段比较长的用户输入用于标题")
    loaded = repo.get_session(session.id)
    assert loaded.title != "新对话"
    assert "…" in loaded.title or len(loaded.title) <= 25


def test_delete_cascade_messages(repo):
    session = repo.create_session()
    repo.add_message(session.id, "user", "x")
    assert repo.delete_session(session.id)
    assert not repo.session_exists(session.id)
