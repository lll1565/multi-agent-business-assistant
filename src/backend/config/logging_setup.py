"""Backend logging —console + rotating file."""

from __future__ import annotations

import logging
import os
import sys
from backend.config.paths import resolve_project_root
from backend.config.structured_log import JsonLogFormatter
from logging.handlers import RotatingFileHandler
from pathlib import Path

_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    *,
    level: str = "INFO",
    log_file: str | Path | None = None,
    console: bool = True,
    log_format: str | None = None,
) -> None:
    """Configure root logging once (console + rotating file)."""
    root = logging.getLogger()
    if root.handlers:
        return

    log_dir = resolve_project_root() / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    file_path = Path(log_file) if log_file else log_dir / "app.log"
    if not file_path.is_absolute():
        file_path = resolve_project_root() / file_path

    log_level = getattr(logging, level.upper(), logging.INFO)
    fmt = (log_format if log_format is not None else os.getenv("LOG_FORMAT", "")).lower()
    use_json = fmt == "json"
    formatter: logging.Formatter
    if use_json:
        formatter = JsonLogFormatter()
    else:
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

    logging.getLogger("app.bootstrap").info(
        "logging ready level=%s file=%s", level.upper(), file_path
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
