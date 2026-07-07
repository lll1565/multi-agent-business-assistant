"""Fast path for simple API doc lookups - skip supervisor LLM round-trips."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from functools import lru_cache
from subagent.config.logging_setup import get_logger
from subagent.stone.routing.classifier import (
    classify_query_agents,
    extract_api_target,
    is_api_doc_only_query,
)
from subagent.stone.routing.registry import SubAgentSpec, discover_stone_agents, get_registry
from subagent.stone.routing.routing_intents import API_LIST_ALL_QUERY_PATTERN
from typing import Any, Protocol

logger = get_logger("agent.api_fastpath")


class InvokableTool(Protocol):
    def invoke(self, input: dict[str, Any], /, **kwargs: Any) -> Any: ...


@dataclass(frozen=True)
class FastPathTools:
    agent_name: str
    query_tool: InvokableTool
    list_all_tool: InvokableTool | None = None


def _load_fast_path_tools(spec: SubAgentSpec) -> FastPathTools | None:
    if not spec.supports_fast_path:
        return None
    if not spec.fast_path_tools:
        logger.warning(
            "fast_path: %s has supports_fast_path but empty fast_path_tools",
            spec.name,
        )
        return None

    module_path = f"subagent.stone.{spec.name}.tools"
    try:
        mod = importlib.import_module(module_path)
    except (ImportError, ModuleNotFoundError) as exc:
        logger.warning(
            "fast_path: skip %s - cannot import %s (%s: %s)",
            spec.name,
            module_path,
            type(exc).__name__,
            exc,
        )
        return None

    resolved: list[InvokableTool] = []
    for tool_name in spec.fast_path_tools:
        tool = getattr(mod, tool_name, None)
        if tool is None:
            logger.warning(
                "fast_path: skip %s - missing tool %r in %s",
                spec.name,
                tool_name,
                module_path,
            )
            return None
        resolved.append(tool)

    query_tool = resolved[0]
    list_all_tool = resolved[1] if len(resolved) > 1 else None
    return FastPathTools(
        agent_name=spec.name,
        query_tool=query_tool,
        list_all_tool=list_all_tool,
    )


def _resolve_fast_path_agent() -> FastPathTools | None:
    discover_stone_agents()
    for spec in get_registry().all():
        tools = _load_fast_path_tools(spec)
        if tools is not None:
            return tools
    return None


@lru_cache(maxsize=1)
def _fast_path_agent() -> FastPathTools | None:
    return _resolve_fast_path_agent()


def clear_fast_path_cache() -> None:
    _fast_path_agent.cache_clear()


def _build_fast_trace(agent_name: str, target: str, reply: str) -> dict[str, Any]:
    preview = reply[:400] + ("..." if len(reply) > 400 else "")
    return {
        "agents_used": [agent_name],
        "agent_labels": [f"{agent_name} fast path"],
        "steps": [
            {
                "type": "delegate",
                "title": f"fast query -> {agent_name}",
                "detail": f"api doc: {target}",
                "agent": agent_name,
            },
            {
                "type": "sub_tool_result",
                "title": f"[{agent_name}] api doc result",
                "detail": preview,
                "agent": agent_name,
            },
        ],
    }


def _build_rescue_trace(agent_name: str, target: str, reply: str) -> dict[str, Any]:
    return {
        "agents_used": [agent_name],
        "agent_labels": [f"API doc Agent ({agent_name})"],
        "steps": [
            {
                "type": "delegate",
                "title": f"delegate -> API doc Agent ({agent_name})",
                "detail": "LLM 失败兜底到本地 API 文档",
                "agent": agent_name,
            },
            {
                "type": "sub_tool",
                "title": f"[API doc Agent ({agent_name})] query",
                "detail": f"api_name: {target or 'list_all'}",
                "agent": agent_name,
            },
            {
                "type": "sub_tool_result",
                "title": f"[API doc Agent ({agent_name})] result",
                "detail": str(reply)[:400],
                "agent": agent_name,
            },
        ],
    }


def invoke_api_doc_tools(
    user_message: str,
    *,
    require_target: bool = True,
    rescue: bool = False,
) -> dict[str, Any] | None:
    resolved = _fast_path_agent()
    if resolved is None:
        return None

    text = user_message.strip()
    target = extract_api_target(text)
    wants_list = bool(API_LIST_ALL_QUERY_PATTERN.search(text))

    if wants_list:
        if resolved.list_all_tool is None:
            logger.warning(
                "fast_path: list-all requested but %s has no list tool",
                resolved.agent_name,
            )
            return None
        reply = str(resolved.list_all_tool.invoke({}))
        trace_builder = _build_rescue_trace if rescue else _build_fast_trace
        return {
            "reply": reply,
            "trace": trace_builder(resolved.agent_name, "all", reply),
        }

    if not target:
        if require_target:
            return None
        logger.info(
            "fast_path: rescue skipped - no endpoint and not a list-all query: %r",
            text[:80],
        )
        return None

    reply = str(resolved.query_tool.invoke({"api_name": target}))
    trace_builder = _build_rescue_trace if rescue else _build_fast_trace
    return {
        "reply": reply,
        "trace": trace_builder(resolved.agent_name, target, reply),
    }


def try_api_doc_fast_path(user_message: str) -> dict[str, Any] | None:
    if not is_api_doc_only_query(user_message):
        return None
    return invoke_api_doc_tools(user_message, require_target=True, rescue=False)


def try_api_doc_rescue(user_message: str) -> dict[str, Any] | None:
    if classify_query_agents(user_message) != ["npi_api_agent"]:
        return None
    return invoke_api_doc_tools(user_message, require_target=True, rescue=True)


__all__ = [
    "FastPathTools",
    "InvokableTool",
    "clear_fast_path_cache",
    "invoke_api_doc_tools",
    "try_api_doc_fast_path",
    "try_api_doc_rescue",
]
