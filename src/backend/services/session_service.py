"""Concrete SessionService."""

from typing import Any

from backend.config.logging_setup import get_logger
from backend.ports.agent import AgentService
from backend.repositories.base import SessionRepository
from backend.repositories.mappers import session_entity_to_dict
from backend.services.base import SessionService

logger = get_logger("backend.session")


class DefaultSessionService(SessionService):
    """Default session service: repository + agent memory cleanup."""

    def __init__(self, repo: SessionRepository, agent: AgentService):
        self._repo = repo
        self._agent = agent

    def list_sessions(self) -> list[dict[str, Any]]:
        return [
            session_entity_to_dict(s, include_messages=False) for s in self._repo.list_sessions()
        ]

    def create_session(self, title: str = "新对话") -> dict[str, Any]:
        session = self._repo.create_session(title=title)
        logger.info("session created id=%s title=%r", session.id, title)
        return session_entity_to_dict(session)

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        session = self._repo.get_session(session_id)
        if session is None:
            return None
        return session_entity_to_dict(session)

    def update_title(self, session_id: str, title: str) -> dict[str, Any] | None:
        if not self._repo.session_exists(session_id):
            return None
        self._repo.update_session_title(session_id, title)
        session = self._repo.get_session(session_id)
        return session_entity_to_dict(session) if session else None

    def delete_session(self, session_id: str) -> bool:
        if not self._repo.delete_session(session_id):
            return False
        try:
            self._agent.clear_session_memory(session_id)
            logger.info("session deleted id=%s (checkpoints cleared)", session_id)
        except Exception as exc:
            logger.warning("checkpoint cleanup failed session=%s: %s", session_id, exc)
        return True

    def ensure_exists(self, session_id: str) -> bool:
        return self._repo.session_exists(session_id)
