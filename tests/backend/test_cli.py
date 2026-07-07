"""Production CLI entry tests."""

from __future__ import annotations

from unittest.mock import patch

from backend.cli import main


def test_multi_agent_backend_cli_invokes_uvicorn() -> None:
    with patch("backend.cli.uvicorn.run") as run:
        main()
    run.assert_called_once()
    args, kwargs = run.call_args
    assert args[0] == "backend.main:app"
    assert kwargs["workers"] == 1
