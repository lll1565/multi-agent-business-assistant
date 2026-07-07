"""Production security — API key auth and chat rate limiting."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.factory import create_app
from backend.app.rate_limit import reset_chat_rate_limiter
from backend.config.settings import clear_backend_settings_cache
from backend.infrastructure.database.engine import create_chat_database, init_schema
from backend.repositories.sqlalchemy_repository import SqlAlchemySessionRepository
from backend.services.chat_service import DefaultChatService
from backend.services.session_service import DefaultSessionService
from tests.conftest import FakeAgentService


def _build_client(tmp_path: Path) -> TestClient:
    db_path = tmp_path / "security_chat.db"
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
    return TestClient(app)


@pytest.fixture
def security_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("API_AUTH_KEY", "test-secret")
    monkeypatch.setenv("CHAT_RATE_LIMIT_PER_MINUTE", "0")
    clear_backend_settings_cache()
    reset_chat_rate_limiter()
    with _build_client(tmp_path) as client:
        yield client
    clear_backend_settings_cache()
    reset_chat_rate_limiter()


def test_health_and_ready_skip_api_key(security_client: TestClient) -> None:
    assert security_client.get("/api/health").status_code == 200
    assert security_client.get("/api/ready").status_code in (200, 503)


def test_api_key_required_for_sessions(security_client: TestClient) -> None:
    denied = security_client.get("/api/sessions")
    assert denied.status_code == 401
    assert denied.json()["code"] == 40100

    allowed = security_client.get("/api/sessions", headers={"X-API-Key": "test-secret"})
    assert allowed.status_code == 200


def test_bearer_api_key(security_client: TestClient) -> None:
    resp = security_client.get(
        "/api/sessions",
        headers={"Authorization": "Bearer test-secret"},
    )
    assert resp.status_code == 200


def test_chat_rate_limit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_AUTH_KEY", "")
    monkeypatch.setenv("CHAT_RATE_LIMIT_PER_MINUTE", "2")
    clear_backend_settings_cache()
    reset_chat_rate_limiter()

    with _build_client(tmp_path) as client:
        session = client.post("/api/sessions", json={"title": "限流"}).json()["data"]
        session_id = session["id"]
        body = {"message": "你好"}

        assert client.post(f"/api/sessions/{session_id}/chat", json=body).status_code == 200
        assert client.post(f"/api/sessions/{session_id}/chat", json=body).status_code == 200
        limited = client.post(f"/api/sessions/{session_id}/chat", json=body)
        assert limited.status_code == 429
        assert limited.json()["code"] == 42900

    clear_backend_settings_cache()
    reset_chat_rate_limiter()
