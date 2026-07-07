"""Agent-layer configuration —LLM, routing, business DB, logging."""

from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from subagent.config.paths import resolve_project_root

_ENV_FILE = resolve_project_root() / ".env"


class AgentSettings(BaseSettings):
    """Settings consumed by subagent.stone and sub-agents."""

    log_level: str = "INFO"
    log_file: str = "data/logs/app.log"
    log_to_console: bool = True

    langsmith_tracing: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "multi-agent-system"
    langsmith_endpoint: str = ""

    otel_enabled: bool = False
    otel_service_name: str = "multi-agent-chat"
    otel_exporter_endpoint: str = ""

    openai_api_key: str = ""
    openai_base_url: str = "https://api.minimaxi.com/v1"
    openai_model: str = "MiniMax-M3"

    db_path: str = "data/demo.db"

    enable_hard_route: bool = True
    reply_buffer_chunk_size: int = Field(
        default=1,
        validation_alias=AliasChoices(
            "reply_buffer_chunk_size",
            "stream_delta_chunk_size",
        ),
    )

    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), extra="ignore")

    @property
    def model_name(self) -> str:
        return self.openai_model

    @property
    def api_key(self) -> str:
        return self.openai_api_key


@lru_cache
def get_agent_settings() -> AgentSettings:
    return AgentSettings()
