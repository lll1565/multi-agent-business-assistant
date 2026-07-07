"""Regression tests for public schema exports and OpenAPI generation."""

from __future__ import annotations

import backend.schemas as schemas
from backend.app.factory import create_app
from backend.schemas import ChatResponse, ReasoningTrace, SessionListData, SessionOut


def test_schema_all_exports_exist():
    assert schemas.__all__
    for name in schemas.__all__:
        assert hasattr(schemas, name), f"backend.schemas.__all__ exports missing name: {name}"


def test_key_schemas_importable():
    assert ChatResponse is schemas.ChatResponse
    assert ReasoningTrace is schemas.ReasoningTrace
    assert SessionListData is schemas.SessionListData
    assert SessionOut is schemas.SessionOut


def test_fastapi_openapi_schema_generates():
    app = create_app()
    spec = app.openapi()
    assert spec["openapi"]
    assert "paths" in spec
    assert "/api/sessions/{session_id}/chat" in spec["paths"]
