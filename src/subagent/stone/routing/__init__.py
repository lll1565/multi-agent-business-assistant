"""Route classification, registry, fast paths, and hard routing."""

from __future__ import annotations

from typing import Any

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    "API_ENDPOINT_NAMES": ("subagent.stone.routing.routing_intents", "API_ENDPOINT_NAMES"),
    "API_LIST_ALL_QUERY_PATTERN": (
        "subagent.stone.routing.routing_intents",
        "API_LIST_ALL_QUERY_PATTERN",
    ),
    "CANCEL_WHEN_DB_INTENT": ("subagent.stone.routing.routing_intents", "CANCEL_WHEN_DB_INTENT"),
    "CANCEL_WHEN_DB_OR_API_INTENT": (
        "subagent.stone.routing.routing_intents",
        "CANCEL_WHEN_DB_OR_API_INTENT",
    ),
    "CANCEL_WHEN_NOT_DIAGRAM": (
        "subagent.stone.routing.routing_intents",
        "CANCEL_WHEN_NOT_DIAGRAM",
    ),
    "DB_TABLE_NAMES": ("subagent.stone.routing.routing_intents", "DB_TABLE_NAMES"),
    "DIAGRAM_EXCLUSIVE_KEYWORDS": (
        "subagent.stone.routing.routing_intents",
        "DIAGRAM_EXCLUSIVE_KEYWORDS",
    ),
    "Keyword": ("subagent.stone.routing.routing_types", "Keyword"),
    "RouteKind": ("subagent.stone.routing.resolve_route", "RouteKind"),
    "SubAgentSpec": ("subagent.stone.routing.registry", "SubAgentSpec"),
    "WEB_EXCLUSIVE_KEYWORDS": (
        "subagent.stone.routing.routing_intents",
        "WEB_EXCLUSIVE_KEYWORDS",
    ),
    "any_keyword_matches": ("subagent.stone.routing.registry", "any_keyword_matches"),
    "build_supervisor_input": ("subagent.stone.routing.classifier", "build_supervisor_input"),
    "cancel_when_db_intent": ("subagent.stone.routing.registry", "cancel_when_db_intent"),
    "cancel_when_db_or_api_intent": (
        "subagent.stone.routing.registry",
        "cancel_when_db_or_api_intent",
    ),
    "cancel_when_not_diagram": ("subagent.stone.routing.registry", "cancel_when_not_diagram"),
    "classify_query": ("subagent.stone.routing.classifier", "classify_query"),
    "classify_query_agents": ("subagent.stone.routing.classifier", "classify_query_agents"),
    "clear_fast_path_cache": ("subagent.stone.routing.api_fastpath", "clear_fast_path_cache"),
    "discover_stone_agents": ("subagent.stone.routing.registry", "discover_stone_agents"),
    "enforce_row_limit": ("subagent.stone.routing.validators", "enforce_row_limit"),
    "extract_api_target": ("subagent.stone.routing.classifier", "extract_api_target"),
    "get_registry": ("subagent.stone.routing.registry", "get_registry"),
    "is_api_doc_only_query": (
        "subagent.stone.routing.classifier",
        "is_api_doc_only_query",
    ),
    "is_meta_query": ("subagent.stone.routing.meta_fastpath", "is_meta_query"),
    "reset_registry": ("subagent.stone.routing.registry", "reset_registry"),
    "resolve_route": ("subagent.stone.routing.resolve_route", "resolve_route"),
    "resolve_route_kind": ("subagent.stone.routing.resolve_route", "resolve_route_kind"),
    "try_api_doc_fast_path": (
        "subagent.stone.routing.api_fastpath",
        "try_api_doc_fast_path",
    ),
    "try_api_doc_rescue": ("subagent.stone.routing.api_fastpath", "try_api_doc_rescue"),
    "try_db_hard_route": ("subagent.stone.routing.hard_route", "try_db_hard_route"),
    "try_meta_fast_path": ("subagent.stone.routing.meta_fastpath", "try_meta_fast_path"),
    "validate_sql": ("subagent.stone.routing.validators", "validate_sql"),
    "validate_user_message": ("subagent.stone.routing.validators", "validate_user_message"),
}

__all__ = list(_LAZY_EXPORTS)


def __getattr__(name: str) -> Any:
    if name not in _LAZY_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr = _LAZY_EXPORTS[name]
    module = __import__(module_name, fromlist=[attr])
    return getattr(module, attr)
