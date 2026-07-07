"""Backend-layer configuration — HTTP, chat DB, logging, tracing."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.config.paths import resolve_project_root
from backend.config.ports import (
    backend_port as _default_backend_port,
)
from backend.config.ports import (
    backend_uvicorn_host as _default_uvicorn_host,
)
from backend.config.ports import (
    default_cors_origins,
)
from backend.config.ports import (
    frontend_port as _default_frontend_port,
)

_ENV_FILE = resolve_project_root() / ".env"


class BackendSettings(BaseSettings):
    """Settings consumed by FastAPI backend."""

    app_env: str = "development"
    backend_port: int = _default_backend_port()
    uvicorn_host: str = _default_uvicorn_host()
    frontend_port: int = _default_frontend_port()

    log_level: str = "INFO"
    log_file: str = "data/logs/app.log"
    log_to_console: bool = True
    log_format: str = ""

    api_auth_key: str = ""
    chat_rate_limit_per_minute: int = 0
    trusted_hosts: str = ""
    serve_frontend: bool = False
    frontend_dist_path: str = "frontend/dist"

    langsmith_tracing: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "multi-agent-system"
    langsmith_endpoint: str = ""

    otel_enabled: bool = False
    otel_service_name: str = "multi-agent-chat"
    otel_exporter_endpoint: str = ""

    chat_db_path: str = "data/chat.db"
    cors_origins: str = default_cors_origins()
    agent_executor_workers: int = 2

    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        raw = (self.cors_origins or "").strip()
        if raw == "*":
            return ["*"]
        return [origin.strip() for origin in raw.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.strip().lower() == "production"

    @property
    def trusted_host_list(self) -> list[str]:
        raw = (self.trusted_hosts or "").strip()
        if not raw:
            return []
        return [host.strip() for host in raw.split(",") if host.strip()]


@lru_cache
def get_backend_settings() -> BackendSettings:
    return BackendSettings()


def clear_backend_settings_cache() -> None:
    get_backend_settings.cache_clear()
