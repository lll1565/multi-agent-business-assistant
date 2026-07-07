"""Shared LangGraph checkpointer (SQLite, survives backend restarts)."""

import sqlite3
from functools import lru_cache

from langgraph.checkpoint.sqlite import SqliteSaver

from subagent.config.paths import resolve_checkpoint_db_path
from subagent.stone.routing.registry import discover_stone_agents, get_registry

_CHECKPOINT_DB = resolve_checkpoint_db_path()


def checkpoint_subagent_names() -> tuple[str, ...]:
    """Sub-agent thread names to purge when a chat session is deleted."""
    discover_stone_agents()
    return tuple(spec.name for spec in get_registry().all() if spec.uses_persistent_checkpointer)


@lru_cache(maxsize=1)
def get_checkpointer() -> SqliteSaver:
    _CHECKPOINT_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_CHECKPOINT_DB), check_same_thread=False)
    return SqliteSaver(conn)


def subagent_thread_id(parent_thread_id: str, agent_name: str) -> str:
    """Isolate sub-agent memory per session without colliding with supervisor."""
    return f"{parent_thread_id}::{agent_name}"


def delete_session_checkpoints(session_id: str) -> None:
    """Remove supervisor + sub-agent checkpoints when a chat session is deleted."""
    saver = get_checkpointer()
    saver.delete_thread(session_id)
    for name in checkpoint_subagent_names():
        saver.delete_thread(subagent_thread_id(session_id, name))
