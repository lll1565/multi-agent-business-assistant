"""Backward-compatible supervisor entry re-exports.

Implementation lives in ``agent_factory``, ``entrypoints``, and ``fallbacks``.
"""

from subagent.stone.runtime.agent_factory import create_supervisor_agent
from subagent.stone.runtime.entrypoints import chat, chat_with_trace, main
from subagent.stone.runtime.fallbacks import (
    _api_doc_fallback,
    _fallback_reply,
    api_doc_fallback,
    fallback_reply,
)

__all__ = [
    "_api_doc_fallback",
    "_fallback_reply",
    "api_doc_fallback",
    "chat",
    "chat_with_trace",
    "create_supervisor_agent",
    "fallback_reply",
    "main",
]


if __name__ == "__main__":
    main()
