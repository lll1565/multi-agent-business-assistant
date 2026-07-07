"""Abstract repositories."""

from abc import ABC, abstractmethod
from typing import Any

from backend.domain.entities import Message, Session


class SessionRepository(ABC):
    """Session and message persistence interface."""

    @abstractmethod
    def init_schema(self) -> None:
        """Initialize database schema."""

    @abstractmethod
    def create_session(self, title: str = "新对话") -> Session:
        pass

    @abstractmethod
    def list_sessions(self, limit: int = 100) -> list[Session]:
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> Session | None:
        pass

    @abstractmethod
    def update_session_title(self, session_id: str, title: str) -> bool:
        pass

    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        pass

    @abstractmethod
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        trace: dict[str, Any] | None = None,
    ) -> Message:
        pass

    @abstractmethod
    def auto_title_from_message(self, session_id: str, message: str) -> None:
        pass

    @abstractmethod
    def session_exists(self, session_id: str) -> bool:
        pass
