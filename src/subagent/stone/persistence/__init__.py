"""Checkpoint storage and SQL demo database tools."""

from __future__ import annotations

from typing import Any

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    "checkpoint_subagent_names": (
        "subagent.stone.persistence.checkpointer",
        "checkpoint_subagent_names",
    ),
    "delete_session_checkpoints": (
        "subagent.stone.persistence.checkpointer",
        "delete_session_checkpoints",
    ),
    "get_checkpointer": ("subagent.stone.persistence.checkpointer", "get_checkpointer"),
    "get_sql_tools": ("subagent.stone.persistence.tools", "get_sql_tools"),
    "subagent_thread_id": ("subagent.stone.persistence.checkpointer", "subagent_thread_id"),
}

__all__ = list(_LAZY_EXPORTS)


def __getattr__(name: str) -> Any:
    if name not in _LAZY_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr = _LAZY_EXPORTS[name]
    module = __import__(module_name, fromlist=[attr])
    return getattr(module, attr)
