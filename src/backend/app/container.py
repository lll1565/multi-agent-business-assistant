"""Dependency injection container."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from backend.adapters.stone_agent import StoneAgentService
from backend.config.paths import resolve_chat_db_path
from backend.config.settings import get_backend_settings
from backend.infrastructure.database.engine import (
    ChatDatabase,
    create_chat_database,
    init_schema,
)
from backend.repositories.sqlalchemy_repository import SqlAlchemySessionRepository
from backend.services.chat_service import DefaultChatService
from backend.services.session_service import DefaultSessionService


@dataclass
class AppContainer:
    """Application-level dependency container."""

    session_service: DefaultSessionService
    chat_service: DefaultChatService
    repo: SqlAlchemySessionRepository
    database: ChatDatabase


def build_container(db_path: Path | str | None = None) -> AppContainer:
    backend_settings = get_backend_settings()
    chat_db = resolve_chat_db_path(db_path or backend_settings.chat_db_path)
    database = create_chat_database(chat_db)
    init_schema(database)

    repo = SqlAlchemySessionRepository(database)
    agent = StoneAgentService()
    executor = ThreadPoolExecutor(max_workers=backend_settings.agent_executor_workers)

    session_service = DefaultSessionService(repo, agent)
    chat_service = DefaultChatService(repo, agent, executor)

    return AppContainer(
        session_service=session_service,
        chat_service=chat_service,
        repo=repo,
        database=database,
    )
