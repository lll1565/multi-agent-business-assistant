"""Agent path resolution (demo DB, checkpoints, project root)."""

from __future__ import annotations

import os
from pathlib import Path

_SUBAGENT_DIR = Path(__file__).resolve().parent.parent
_DEFAULT_ROOT = _SUBAGENT_DIR.parent.parent


def resolve_project_root() -> Path:
    raw = os.environ.get("PROJECT_ROOT", str(_DEFAULT_ROOT))
    return Path(raw).expanduser().resolve()


def resolve_data_dir(project_root: Path | None = None) -> Path:
    if "DATA_DIR" in os.environ:
        return Path(os.environ["DATA_DIR"]).expanduser().resolve()
    root = project_root or resolve_project_root()
    return (root / "data").resolve()


PROJECT_ROOT = resolve_project_root()
DATA_DIR = resolve_data_dir(PROJECT_ROOT)


def _resolve_under_project_root(
    path: str | Path | None,
    default_relative: str,
) -> Path:
    root = resolve_project_root()
    raw = Path(path) if path else Path(default_relative)
    if not raw.is_absolute():
        raw = root / raw
    return raw.resolve()


def resolve_demo_db_path(db_path: str | Path | None = None) -> Path:
    return _resolve_under_project_root(db_path, "data/demo.db")


def resolve_checkpoint_db_path(db_path: str | Path | None = None) -> Path:
    if db_path is not None:
        return _resolve_under_project_root(db_path, "data/agent_checkpoints.db")
    return (resolve_data_dir() / "agent_checkpoints.db").resolve()


__all__ = [
    "DATA_DIR",
    "PROJECT_ROOT",
    "resolve_checkpoint_db_path",
    "resolve_data_dir",
    "resolve_demo_db_path",
    "resolve_project_root",
]
