"""Stone supervisor package - lazy imports to avoid loading deepagents at import time."""

__all__ = ["chat", "create_supervisor_agent"]


def __getattr__(name: str):
    if name == "chat":
        from subagent.stone.runtime.core import chat

        return chat
    if name == "create_supervisor_agent":
        from subagent.stone.runtime.core import create_supervisor_agent

        return create_supervisor_agent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
