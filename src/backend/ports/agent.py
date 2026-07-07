"""Agent capability port - backend invokes intelligence via this interface."""

from abc import ABC, abstractmethod
from collections.abc import Iterator

from subagent.stone.runtime.contracts import StreamEvent, TurnResult


class AgentService(ABC):
    """Multi-agent invocation abstraction."""

    @abstractmethod
    def invoke(self, message: str, session_id: str, request_id: str) -> TurnResult:
        """Synchronous invoke returning TurnResult."""
        pass

    @abstractmethod
    def stream_events(
        self, message: str, session_id: str, request_id: str
    ) -> Iterator[StreamEvent]:
        """Streaming event iterator (SSE source)."""
        pass

    @abstractmethod
    def clear_session_memory(self, session_id: str) -> None:
        """Clear agent checkpoint memory for a session."""
        pass
