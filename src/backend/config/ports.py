"""Dev server ports —shared by backend, frontend (Vite), and PowerShell scripts."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

_PORTS_FILE = Path(__file__).resolve().parent / "ports.json"


@lru_cache(maxsize=1)
def load_ports() -> dict[str, Any]:
    with _PORTS_FILE.open(encoding="utf-8") as fh:
        return cast(dict[str, Any], json.load(fh))


def backend_port() -> int:
    return int(load_ports()["backend"]["port"])


def backend_host() -> str:
    return str(load_ports()["backend"]["host"])


def backend_uvicorn_host() -> str:
    return str(load_ports()["backend"].get("uvicorn_host", "0.0.0.0"))


def frontend_port() -> int:
    return int(load_ports()["frontend"]["port"])


def frontend_host() -> str:
    return str(load_ports()["frontend"]["host"])


def frontend_origin() -> str:
    host = frontend_host()
    if host == "0.0.0.0":
        host = "127.0.0.1"
    return f"http://{host}:{frontend_port()}"


def default_cors_origins() -> str:
    port = frontend_port()
    return f"http://localhost:{port},http://127.0.0.1:{port}"
