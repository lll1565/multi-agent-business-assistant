"""Abstract services."""

from abc import ABC, abstractmethod
from backend.schemas import ChatResponse, ReasoningTrace
from collections.abc import Iterator
from typing import Any

__all__ = ["ChatService", "SessionService"]


class SessionService(ABC):
    """Session CRUD abstraction."""

    @abstractmethod
    def list_sessions(self) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    def create_session(self, title: str = "新对话") -> dict[str, Any]:
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> dict[str, Any] | None:
        pass

    @abstractmethod
    def update_title(self, session_id: str, title: str) -> dict[str, Any] | None:
        pass

    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        pass

    @abstractmethod
    def ensure_exists(self, session_id: str) -> bool:
        pass


class ChatService(ABC):
    """Chat orchestration: persistence + agent invocation."""

    @abstractmethod
    async def chat(self, session_id: str, message: str, request_id: str) -> ChatResponse:
        pass

    @abstractmethod
    def chat_stream(self, session_id: str, message: str, request_id: str) -> Iterator[str]:
        """Return SSE lines (data: ...\\n\\n)."""
        pass

    @abstractmethod
    async def chat_legacy(self, message: str, request_id: str) -> ChatResponse:
        pass

    @staticmethod
    def build_trace(trace_data: dict[str, Any] | None) -> ReasoningTrace | None:
        if not trace_data:
            return None
        from backend.schemas import ReasoningStep

        return ReasoningTrace(
            agents_used=trace_data.get("agents_used", []),
            agent_labels=trace_data.get("agent_labels", []),
            steps=[ReasoningStep(**s) for s in trace_data.get("steps", [])],
        )
