"""Deterministic routing — invoke sub-agents directly when classification is unambiguous.

The route target is resolved from the registry by `kind` and `supports_hard_route`,
so adding a new hard-routable agent is a registry-only change.
"""

from __future__ import annotations

from functools import lru_cache
from langchain_core.messages import HumanMessage
from langchain_core.runnables import Runnable
from langchain_core.runnables.config import RunnableConfig
from subagent.config.logging_setup import get_logger
from subagent.config.settings import get_agent_settings
from subagent.stone.persistence.checkpointer import subagent_thread_id
from subagent.stone.routing.classifier import classify_query_agents
from subagent.stone.routing.registry import (
    SubAgentSpec,
    discover_stone_agents,
    get_registry,
)
from subagent.stone.runtime.subagent_wrapper import (
    begin_nested_trace_capture,
    end_nested_trace_capture,
    wrap_subagent_runnable,
)
from subagent.stone.runtime.trace import AGENT_LABELS, extract_reply, merge_nested_traces
from typing import Any, cast

settings = get_agent_settings()
logger = get_logger("agent.hard_route")


def _find_hard_route_spec(kind: str) -> SubAgentSpec | None:
    """Return the first registered spec matching `kind` and `supports_hard_route=True`."""
    discover_stone_agents()
    for spec in get_registry().all():
        if spec.kind == kind and spec.supports_hard_route:
            return spec
    return None


@lru_cache(maxsize=8)
def _get_agent_runnable(agent_name: str) -> Runnable[Any, Any]:
    """Cache wrapped runnables per agent name (one wrapped instance per agent)."""
    spec = get_registry().get(agent_name)
    if spec is None:
        raise ValueError(f"hard_route: agent {agent_name!r} not in registry")
    return cast(Runnable[Any, Any], wrap_subagent_runnable(spec.factory(), agent_name))


def _subagent_config(session_id: str | None, agent_name: str) -> dict[str, Any] | None:
    if not session_id:
        return None
    return {
        "configurable": {
            "thread_id": subagent_thread_id(session_id, agent_name),
        }
    }


def _wrap_hard_trace(agent_name: str, nested_traces: list[dict[str, Any]]) -> dict[str, Any]:
    label = AGENT_LABELS.get(agent_name, agent_name)
    base = {
        "agents_used": [agent_name],
        "agent_labels": [label],
        "steps": [
            {
                "type": "delegate",
                "title": f"硬路由 → {label}",
                "detail": f"高置信度分类为 {agent_name}，跳过 Supervisor 直接委派",
                "agent": agent_name,
            }
        ],
    }
    return cast(dict[str, Any], merge_nested_traces(base, nested_traces))


def _extract_reply_text(messages: list[Any]) -> str:
    extracted = extract_reply(messages)
    if isinstance(extracted, str) and extracted:
        return extracted
    if not messages:
        return ""
    last = messages[-1]
    content = getattr(last, "content", "") or ""
    return str(content)


def try_hard_route(
    user_message: str,
    kind: str = "db",
    session_id: str | None = None,
    request_id: str | None = None,
) -> dict[str, Any] | None:
    """Dispatch a high-confidence `kind` query directly to the matching agent.

    Returns ``None`` when hard routing is disabled, classification is not
    exactly `kind`, or no registered spec advertises that combination.
    """
    if not settings.enable_hard_route:
        return None
    spec = _find_hard_route_spec(kind)
    if spec is None:
        return None
    if classify_query_agents(user_message) != [spec.name]:
        return None

    rid = request_id or "-"
    logger.info("[%s] hard route agent=%s kind=%s session=%s", rid, spec.name, kind, session_id)

    runnable = _get_agent_runnable(spec.name)
    config = cast(RunnableConfig | None, _subagent_config(session_id, spec.name))
    bucket = begin_nested_trace_capture()
    try:
        result = runnable.invoke(
            {"messages": [HumanMessage(content=user_message)]},
            config=config,
        )
    finally:
        nested = end_nested_trace_capture(bucket)

    messages = result.get("messages") or []
    reply = _extract_reply_text(messages)

    return {
        "reply": reply,
        "trace": _wrap_hard_trace(spec.name, nested),
    }


def try_db_hard_route(
    user_message: str,
    session_id: str | None = None,
    request_id: str | None = None,
) -> dict[str, Any] | None:
    """Backward-compatible alias for `try_hard_route(kind="db")`."""
    return try_hard_route(
        user_message,
        kind="db",
        session_id=session_id,
        request_id=request_id,
    )


__all__ = ["try_db_hard_route", "try_hard_route"]
