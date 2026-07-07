"""Tests for delete_session_checkpoints."""

from __future__ import annotations

import subagent.stone.persistence.checkpointer as checkpointer


def test_delete_session_checkpoints_purges_supervisor_and_subagents(monkeypatch):
    deleted: list[str] = []

    def fake_delete_thread(thread_id: str) -> None:
        deleted.append(thread_id)

    saver = checkpointer.get_checkpointer()
    monkeypatch.setattr(saver, "delete_thread", fake_delete_thread)

    checkpointer.delete_session_checkpoints("sess-xyz")

    assert "sess-xyz" in deleted
    assert "sess-xyz::npi_db_agent" in deleted
    assert "sess-xyz::npi_api_agent" in deleted
    assert "sess-xyz::npi_web_agent" not in deleted
    assert "sess-xyz::npi_diagram_agent" not in deleted
