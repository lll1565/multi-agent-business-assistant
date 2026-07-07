"""FastAPI integration tests — session CRUD + chat with stub agent."""


def _data(resp):
    body = resp.json()
    assert body.get("code") == 0, body
    return body["data"]


def test_root_envelope(api_client):
    resp = api_client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["message"] == "Multi-Agent Chat API"
    assert body["data"]["docs"] == "/api/docs"


def test_health(api_client):
    resp = api_client.get("/api/health")
    assert resp.status_code == 200
    assert _data(resp)["status"] == "ok"


def test_ready(api_client):
    resp = api_client.get("/api/ready")
    assert resp.status_code in (200, 503)
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["status"] in ("ready", "not_ready")
    assert isinstance(data["checks"], list)
    assert any(c["name"] == "chat_database" for c in data["checks"])


def test_session_crud_flow(api_client):
    create = api_client.post("/api/sessions", json={"title": "集成测试"})
    assert create.status_code == 200
    created = _data(create)
    session_id = created["id"]
    assert created["title"] == "集成测试"

    listing = api_client.get("/api/sessions")
    assert listing.status_code == 200
    assert any(s["id"] == session_id for s in _data(listing)["sessions"])

    detail = api_client.get(f"/api/sessions/{session_id}")
    assert detail.status_code == 200
    assert _data(detail)["messages"] == []

    patched = api_client.patch(
        f"/api/sessions/{session_id}",
        json={"title": "新标题"},
    )
    assert patched.status_code == 200
    assert _data(patched)["title"] == "新标题"

    deleted = api_client.delete(f"/api/sessions/{session_id}")
    assert deleted.status_code == 200
    assert _data(deleted)["ok"] is True

    missing = api_client.get(f"/api/sessions/{session_id}")
    assert missing.status_code == 404
    assert missing.json()["code"] == 40401


def test_chat_rejects_empty_message(api_client):
    session = _data(api_client.post("/api/sessions"))
    resp = api_client.post(
        f"/api/sessions/{session['id']}/chat",
        json={"message": "   "},
    )
    assert resp.status_code == 422
    assert resp.json()["code"] == 42200


def test_chat_sync_with_stub_agent(api_client):
    session = _data(api_client.post("/api/sessions"))
    resp = api_client.post(
        f"/api/sessions/{session['id']}/chat",
        json={"message": "你好"},
    )
    assert resp.status_code == 200
    body = _data(resp)
    assert body["success"] is True
    assert body["reply"] == "测试回复"

    detail = api_client.get(f"/api/sessions/{session['id']}")
    messages = _data(detail)["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "你好"
