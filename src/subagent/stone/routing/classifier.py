"""Lightweight routing hints - data-driven from the subagent registry."""

from __future__ import annotations

import re

from subagent.stone.routing.registry import (
    any_keyword_matches,
    discover_stone_agents,
    get_registry,
)
from subagent.stone.routing.routing_intents import API_ENDPOINT_NAMES


def classify_query_agents(message: str) -> list[str]:
    text = (message or "").strip()
    if not text:
        return []

    discover_stone_agents()
    registry = get_registry()

    basic_hits: list[str] = [
        spec.name
        for spec in registry.all()
        if spec.keywords and any_keyword_matches(spec.keywords, text)
    ]

    for spec in registry.all():
        if not spec.exclusive_keywords:
            continue
        if not any_keyword_matches(spec.exclusive_keywords, text):
            continue
        if spec.exclusive_cancel_keywords and any_keyword_matches(
            spec.exclusive_cancel_keywords, text
        ):
            continue
        return [spec.name]

    return basic_hits


def classify_query(message: str) -> str | None:
    agents = set(classify_query_agents(message))
    has_db = "npi_db_agent" in agents
    has_api = "npi_api_agent" in agents
    if has_db and has_api:
        return "both"
    if has_db:
        return "db"
    if has_api:
        return "api"
    return None


def is_api_doc_only_query(message: str) -> bool:
    return classify_query_agents(message) == ["npi_api_agent"]


def extract_api_target(message: str) -> str | None:
    text = (message or "").lower()
    endpoints: tuple[str, ...] = API_ENDPOINT_NAMES
    for name in endpoints:
        if name in text:
            return name
    m = re.search(r"/api/([a-z0-9_]+)", text)
    if m is None:
        return None
    endpoint = m.group(1)
    assert isinstance(endpoint, str)
    return endpoint


def get_routing_hint(message: str) -> str | None:
    agents = classify_query_agents(message)
    if not agents:
        return None

    agent_set = set(agents)
    has_db = "npi_db_agent" in agent_set
    has_api = "npi_api_agent" in agent_set

    if has_db and not has_api and len(agents) == 1:
        return (
            "用户意图偏数据库/SQL 查询。请用 task 委派 **npi_db_agent**。"
            "只读 SQL，默认返回不超过 5 行。"
        )
    if has_api and not has_db and len(agents) == 1:
        return (
            "用户意图偏 API 文档查询。请委派 **npi_api_agent**，不要调用 npi_db_agent。"
            "返回完整接口文档（含表格与响应示例）。"
        )
    if has_db and has_api and set(agents) <= {"npi_db_agent", "npi_api_agent"}:
        return (
            "用户同时涉及数据库与 API。请分别 task 委派 "
            "**npi_db_agent** 与 **npi_api_agent**，合并结果。"
        )

    if len(agents) == 1:
        return f"用户意图适合 {agents[0]}。请用 task 委派 **{agents[0]}**，返回完整正文。"
    joined = " 与 ".join(f"**{name}**" for name in agents)
    return f"用户意图涉及 {len(agents)} 个领域。请分别 task 委派 {joined}，合并结果。"


def build_supervisor_input(user_message: str) -> str:
    from subagent.stone.routing.meta_fastpath import is_meta_query

    if is_meta_query(user_message):
        return (
            "[路由提示] 这是问候/能力咨询类问题，不要委派任何 Agent。"
            "直接简洁回答即可，不要暴露内部架构名。\n\n"
            f"用户：{user_message}"
        )

    hint = get_routing_hint(user_message)
    if not hint:
        return user_message
    return f"[路由提示] {hint}\n\n用户：{user_message}"


__all__ = [
    "build_supervisor_input",
    "classify_query",
    "classify_query_agents",
    "extract_api_target",
    "get_routing_hint",
    "is_api_doc_only_query",
]
