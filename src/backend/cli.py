"""Production console entry — `multi-agent-backend`."""

from __future__ import annotations

import uvicorn

from backend.config.settings import get_backend_settings


def main() -> None:
    settings = get_backend_settings()
    uvicorn.run(
        "backend.main:app",
        host=settings.uvicorn_host,
        port=settings.backend_port,
        workers=1,
        log_level=settings.log_level.lower(),
        proxy_headers=True,
        forwarded_allow_ips="*",
    )


if __name__ == "__main__":
    main()
