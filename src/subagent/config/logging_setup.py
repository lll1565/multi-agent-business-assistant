"""Agent logging —used by CLI and standalone agent runs."""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from subagent.config.paths import resolve_project_root

_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    *,
    level: str = "INFO",
    log_file: str | Path | None = None,
    console: bool = True,
) -> None:
    root = logging.getLogger()
    if root.handlers:
        return

    project_root = resolve_project_root()
    log_dir = project_root / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    file_path = Path(log_file) if log_file else log_dir / "app.log"
    if not file_path.is_absolute():
        file_path = project_root / file_path

    log_level = getattr(logging, level.upper(), logging.INFO)
    formatter = logging.Formatter(_FORMAT, datefmt=_DATE_FMT)
    root.setLevel(log_level)

    if console:
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(formatter)
        sh.setLevel(log_level)
        root.addHandler(sh)

    fh = RotatingFileHandler(
        file_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    fh.setFormatter(formatter)
    fh.setLevel(log_level)
    root.addHandler(fh)

    for noisy in ("httpx", "httpcore", "urllib3", "openai", "langchain"):
        logging.getLogger(noisy).setLevel(
            logging.DEBUG if log_level <= logging.DEBUG else logging.WARNING
        )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
