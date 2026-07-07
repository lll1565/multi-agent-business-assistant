"""Tests for tracing configuration."""

from backend.config.settings import BackendSettings
from backend.config.tracing import configure_tracing, current_trace_id, span


def test_configure_tracing_disabled_by_default():
    flags = configure_tracing(BackendSettings())
    assert flags == {"langsmith": False, "otel": False}
    assert current_trace_id() is None


def test_configure_langsmith_sets_env(monkeypatch):
    monkeypatch.delenv("LANGCHAIN_TRACING_V2", raising=False)
    settings = BackendSettings(
        langsmith_tracing=True,
        langsmith_api_key="test-key",
        langsmith_project="demo-project",
    )
    flags = configure_tracing(settings)
    assert flags["langsmith"] is True
    import os

    assert os.environ.get("LANGCHAIN_TRACING_V2") == "true"
    assert os.environ.get("LANGCHAIN_API_KEY") == "test-key"
    assert os.environ.get("LANGCHAIN_PROJECT") == "demo-project"


def test_span_noop_when_otel_disabled():
    with span("test.noop", attributes={"x": 1}) as s:
        assert s is None
