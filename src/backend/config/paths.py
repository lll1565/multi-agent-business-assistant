"""Backend path resolution (chat DB, project root, data dir)."""

from __future__ import annotations

import os
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_src_dir = _BACKEND_DIR.parent
_DEFAULT_ROOT = _src_dir.parent if _src_dir.name == "src" else _BACKEND_DIR.parent


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


def resolve_chat_db_path(db_path: str | Path | None = None) -> Path:
    """Absolute path to chat DB (default data/chat.db)."""
    return _resolve_under_project_root(db_path, "data/chat.db")


__all__ = [
    "DATA_DIR",
    "PROJECT_ROOT",
    "resolve_chat_db_path",
    "resolve_data_dir",
    "resolve_project_root",
]
