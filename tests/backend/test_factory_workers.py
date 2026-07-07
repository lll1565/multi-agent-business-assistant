"""Startup policy tests (single-worker requirement)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def test_lifespan_rejects_multi_worker(monkeypatch):
    monkeypatch.setenv("UVICORN_WORKERS", "4")
    from backend.app.factory import create_app

    with pytest.raises(RuntimeError, match="UVICORN_WORKERS"):
        with TestClient(create_app()):
            pass


def test_lifespan_allows_single_worker(monkeypatch):
    monkeypatch.setenv("UVICORN_WORKERS", "1")
    from backend.app.factory import create_app

    with TestClient(create_app()) as client:
        assert client.get("/").status_code == 200
