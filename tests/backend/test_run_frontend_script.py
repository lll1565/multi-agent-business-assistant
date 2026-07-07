"""Regression tests for the Windows frontend launcher script."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "run_frontend.ps1"


def test_run_frontend_script_uses_project_frontend_path():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "$ScriptDir" in text
    assert "$PSScriptRoot" in text
    assert "Join-Path $ProjectRoot \"frontend\"" in text
    assert "Join-Path $FrontendDir \"package.json\"" in text
    assert "Test-Path -LiteralPath $PackageJson -PathType Leaf" in text
    assert "exit 1" in text


def test_run_frontend_path_calculation_matches_repo_layout():
    script_dir = SCRIPT.parent
    root = script_dir.parent
    frontend_dir = root / "frontend"
    assert root == ROOT
    assert (frontend_dir / "package.json").is_file()
