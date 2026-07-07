"""Serve built Vue frontend from FastAPI (single-container production)."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from starlette.staticfiles import StaticFiles

from backend.config.logging_setup import get_logger

logger = get_logger("backend.static")


def mount_frontend(app: FastAPI, dist_dir: Path) -> None:
    """Mount SPA assets; API routes must already be registered under /api."""
    if not dist_dir.is_dir():
        logger.warning("serve_frontend enabled but dist missing: %s", dist_dir)
        return

    assets_dir = dist_dir / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

    index_file = dist_dir / "index.html"

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str) -> FileResponse:
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="Not Found")
        candidate = dist_dir / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        if index_file.is_file():
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Not Found")

    logger.info("frontend static mounted from %s", dist_dir)
