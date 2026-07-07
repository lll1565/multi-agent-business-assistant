"""Tests for shared path resolution."""

from pathlib import Path

from backend.config.paths import resolve_chat_db_path
from subagent.config.paths import (
    resolve_checkpoint_db_path,
    resolve_data_dir,
    resolve_demo_db_path,
    resolve_project_root,
)


def test_resolve_project_root_env_override(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("PROJECT_ROOT", str(tmp_path))
    assert resolve_project_root() == tmp_path.resolve()


def test_resolve_data_dir_env_override(monkeypatch, tmp_path: Path):
    custom = tmp_path / "runtime"
    monkeypatch.setenv("DATA_DIR", str(custom))
    assert resolve_data_dir() == custom.resolve()


def test_resolve_data_dir_default_under_project_root(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("DATA_DIR", raising=False)
    monkeypatch.setenv("PROJECT_ROOT", str(tmp_path))
    assert resolve_data_dir(resolve_project_root()) == (tmp_path / "data").resolve()


def test_resolve_demo_db_default_under_project_root(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("PROJECT_ROOT", str(tmp_path))
    assert resolve_demo_db_path() == (tmp_path / "data" / "demo.db").resolve()


def test_resolve_demo_db_relative_override(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("PROJECT_ROOT", str(tmp_path))
    assert resolve_demo_db_path("custom/biz.db") == (tmp_path / "custom" / "biz.db").resolve()


def test_resolve_checkpoint_db_default(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("PROJECT_ROOT", str(tmp_path))
    monkeypatch.delenv("DATA_DIR", raising=False)
    assert resolve_checkpoint_db_path() == (tmp_path / "data" / "agent_checkpoints.db").resolve()


def test_resolve_chat_db_default(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("PROJECT_ROOT", str(tmp_path))
    monkeypatch.delenv("DATA_DIR", raising=False)
    assert resolve_chat_db_path() == (tmp_path / "data" / "chat.db").resolve()


def test_resolve_chat_db_backend_setting_style(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("PROJECT_ROOT", str(tmp_path))
    assert resolve_chat_db_path("data/chat.db") == (tmp_path / "data" / "chat.db").resolve()
