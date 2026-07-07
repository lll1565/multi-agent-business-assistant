"""Tests for LangGraph checkpoint helpers."""

from dataclasses import replace

from subagent.stone.persistence.checkpointer import checkpoint_subagent_names, subagent_thread_id
from subagent.stone.routing.registry import discover_stone_agents, get_registry


def test_checkpoint_subagent_names_from_registry():
    names = checkpoint_subagent_names()
    assert "npi_db_agent" in names
    assert "npi_api_agent" in names
    assert "npi_web_agent" not in names
    assert "npi_diagram_agent" not in names


def test_checkpoint_subagent_names_matches_persistent_flag():
    discover_stone_agents()
    expected = tuple(
        spec.name for spec in get_registry().all() if spec.uses_persistent_checkpointer
    )
    assert checkpoint_subagent_names() == expected
    assert set(expected) == {"npi_db_agent", "npi_api_agent"}


def test_checkpoint_subagent_names_excludes_when_flag_cleared(monkeypatch):
    discover_stone_agents()
    registry = get_registry()
    db_spec = registry.get("npi_db_agent")
    assert db_spec is not None
    assert db_spec.uses_persistent_checkpointer is True

    broken_db = replace(db_spec, uses_persistent_checkpointer=False)
    original_specs = registry.all()

    def _all_without_db_flag() -> tuple:
        return tuple(broken_db if spec.name == "npi_db_agent" else spec for spec in original_specs)

    monkeypatch.setattr(registry, "all", _all_without_db_flag)

    names = checkpoint_subagent_names()
    assert "npi_db_agent" not in names
    assert names == ("npi_api_agent",)


def test_subagent_thread_id_format():
    assert subagent_thread_id("sess-1", "npi_db_agent") == "sess-1::npi_db_agent"
