"""FastAPI entrypoint."""

from backend.app.factory import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn

    from backend.config.settings import get_backend_settings

    backend_settings = get_backend_settings()

    uvicorn.run(
        "backend.main:app",
        host=backend_settings.uvicorn_host,
        port=backend_settings.backend_port,
        reload=True,
        reload_dirs=["backend"],
        log_level=backend_settings.log_level.lower(),
    )
