"""Unified route resolution ? single entry for sync and streaming chat paths."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from subagent.config.logging_setup import get_logger
from subagent.config.settings import get_agent_settings
from subagent.stone.routing.api_fastpath import _fast_path_agent, try_api_doc_fast_path
from subagent.stone.routing.classifier import (
    classify_query_agents,
    extract_api_target,
    get_routing_hint,
    is_api_doc_only_query,
)
from subagent.stone.routing.hard_route import _find_hard_route_spec, try_db_hard_route
from subagent.stone.routing.meta_fastpath import is_meta_query, try_meta_fast_path
from subagent.stone.routing.routing_intents import API_LIST_ALL_QUERY_PATTERN
from subagent.stone.routing.validators import validate_user_message
from typing import Any

settings = get_agent_settings()
logger = get_logger("agent.resolve_route")


class RouteKind(str, Enum):
    INVALID = "invalid"
    META_FAST = "meta_fast"
    API_FAST = "api_fast"
    HARD_DB = "hard_db"
    SUPERVISOR = "supervisor"


@dataclass(frozen=True)
class RouteDecision:
    """Outcome of routing a user turn before (or instead of) supervisor invoke."""

    kind: RouteKind
    result: dict[str, Any] | None = None
    validation_error: str | None = None
    routing_hint: str | None = None


def _would_api_fast_path(message: str) -> bool:
    """Dry-run: would api_fastpath return a result (no tool invocation)?"""
    if not is_api_doc_only_query(message):
        return False
    if _fast_path_agent() is None:
        return False
    text = message.strip()
    target = extract_api_target(text)
    if not target and API_LIST_ALL_QUERY_PATTERN.search(text):
        return True
    return bool(target)


def _would_hard_db_route(message: str) -> bool:
    """Dry-run: would db hard route apply (no sub-agent invocation)?"""
    if not settings.enable_hard_route:
        return False
    if classify_query_agents(message) != ["npi_db_agent"]:
        return False
    return _find_hard_route_spec("db") is not None


def resolve_route_kind(message: str) -> RouteKind:
    """Classify route without invoking sub-agents (for golden tests)."""
    ok, _err = validate_user_message(message)
    if not ok:
        return RouteKind.INVALID
    if is_meta_query(message):
        return RouteKind.META_FAST
    if _would_api_fast_path(message):
        return RouteKind.API_FAST
    if _would_hard_db_route(message):
        return RouteKind.HARD_DB
    return RouteKind.SUPERVISOR


def resolve_route(
    user_message: str,
    session_id: str | None = None,
    request_id: str | None = None,
) -> RouteDecision:
    """Resolve and execute fast/hard paths; supervisor path returns hint only."""
    rid = request_id or "-"
    ok, err = validate_user_message(user_message)
    if not ok:
        logger.warning("[%s] invalid input: %s", rid, err)
        return RouteDecision(kind=RouteKind.INVALID, validation_error=err)

    meta = try_meta_fast_path(user_message)
    if meta:
        logger.info("[%s] route=meta_fast session=%s", rid, session_id)
        return RouteDecision(kind=RouteKind.META_FAST, result=meta)

    fast = try_api_doc_fast_path(user_message)
    if fast:
        logger.info("[%s] route=api_fast session=%s", rid, session_id)
        return RouteDecision(kind=RouteKind.API_FAST, result=fast)

    hard = try_db_hard_route(
        user_message,
        session_id=session_id,
        request_id=rid,
    )
    if hard:
        logger.info("[%s] route=hard_db session=%s", rid, session_id)
        return RouteDecision(kind=RouteKind.HARD_DB, result=hard)

    hint = get_routing_hint(user_message)
    logger.info("[%s] route=supervisor session=%s hint=%r", rid, session_id, hint)
    return RouteDecision(kind=RouteKind.SUPERVISOR, routing_hint=hint)


__all__ = ["RouteDecision", "RouteKind", "resolve_route", "resolve_route_kind"]
