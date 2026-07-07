"""Architecture boundary tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _lint_imports_cmd() -> list[str]:
    exe = Path(sys.executable).with_name("lint-imports.exe")
    if exe.exists():
        return [str(exe)]
    return ["lint-imports"]


def test_subagent_must_not_import_backend():
    result = subprocess.run(
        _lint_imports_cmd(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
