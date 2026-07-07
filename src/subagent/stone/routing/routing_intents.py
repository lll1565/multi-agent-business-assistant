"""Shared routing vocabulary — single source for cross-agent keywords.

Agent packages import endpoint/table names, exclusive overrides, and cancel
lists from here so routing stays in sync when the demo DB or API catalog changes.
"""

from __future__ import annotations

import re
from subagent.stone.routing.routing_types import Keyword

API_ENDPOINT_NAMES: tuple[str, ...] = (
    "get_users",
    "get_user",
    "create_user",
    "update_user",
    "delete_user",
    "login",
)

# Strong API-doc signals for *exclusive* routing (hard override).
# Deliberately excludes update/delete/login — those appear in mixed DB+API queries
# more often and are already covered by basic keyword hits on the full list.
API_ENDPOINT_NAMES_EXCLUSIVE: tuple[str, ...] = (
    "get_users",
    "get_user",
    "create_user",
)

DB_TABLE_NAMES: tuple[str, ...] = (
    "categories",
    "suppliers",
    "products",
    "customers",
    "orders",
    "order_items",
    "payments",
    "inventory",
)

DB_INTENT_TERMS: tuple[Keyword, ...] = (
    "数据库",
    "数据表",
    "表结构",
    "sql",
    "demo.db",
    *DB_TABLE_NAMES,
)

API_DOC_INTENT_TERMS: tuple[Keyword, ...] = (
    "api",
    "接口",
    "rest",
    "接口文档",
    re.compile(r"api\s*文档", re.IGNORECASE),
    re.compile(r"api\s*doc", re.IGNORECASE),
    re.compile(r"/api/"),
    *API_ENDPOINT_NAMES,
)

WEB_INTENT_TERMS: tuple[str, ...] = (
    "网上",
    "联网",
    "联网搜",
    "搜索",
)

# Matches "list all APIs" style queries (shared by api_fastpath + resolve_route dry-run).
API_LIST_ALL_QUERY_PATTERN = re.compile(
    "\u6240\u6709|\u5168\u90e8|\u5217\u8868|\u6709\u54ea\u4e9b\u63a5\u53e3"
)

CANCEL_WHEN_DB_INTENT: tuple[Keyword, ...] = DB_INTENT_TERMS

CANCEL_WHEN_DB_OR_API_INTENT: tuple[Keyword, ...] = (
    *DB_INTENT_TERMS,
    "接口文档",
    *API_ENDPOINT_NAMES,
)

CANCEL_WHEN_NOT_DIAGRAM: tuple[Keyword, ...] = (
    "数据库",
    "数据表",
    "sql",
    "demo.db",
    "接口文档",
    "get_users",
    "get_user",
    "login",
    "网上",
    "联网搜",
)

API_EXCLUSIVE_KEYWORDS: tuple[Keyword, ...] = (
    re.compile(r"api\s*文档", re.IGNORECASE),
    re.compile(r"接口文档"),
    re.compile(r"api\s*doc", re.IGNORECASE),
    *API_ENDPOINT_NAMES_EXCLUSIVE,
    re.compile(r"/api/[a-z0-9_/{}/-]+"),
)

WEB_EXCLUSIVE_KEYWORDS: tuple[Keyword, ...] = (
    "网上",
    "联网",
    "搜索",
    re.compile(r"^网上\s"),
    re.compile(r"^search\s+the\s+web", re.IGNORECASE),
    re.compile(r"^look\s+up", re.IGNORECASE),
)

DIAGRAM_EXCLUSIVE_KEYWORDS: tuple[Keyword, ...] = (
    re.compile(r"画\s*(?:一|个|张|幅)?.*(?:图|chart|diagram)"),
    re.compile(r"(?:draw|render|plot)\s+(?:a|an|the)\s+\w+\s+(?:diagram|chart|graph)"),
    re.compile(r"帮我\s*(?:画|绘|做|生成)?"),
    re.compile(r"^画\s*"),
    re.compile(r"^绘制\s*"),
    re.compile(r"^生成\s*"),
    "流程图",
    "架构图",
    "时序图",
    "画 ER 图",
)

__all__ = [
    "API_DOC_INTENT_TERMS",
    "API_ENDPOINT_NAMES",
    "API_ENDPOINT_NAMES_EXCLUSIVE",
    "API_EXCLUSIVE_KEYWORDS",
    "API_LIST_ALL_QUERY_PATTERN",
    "CANCEL_WHEN_DB_INTENT",
    "CANCEL_WHEN_DB_OR_API_INTENT",
    "CANCEL_WHEN_NOT_DIAGRAM",
    "DB_INTENT_TERMS",
    "DB_TABLE_NAMES",
    "DIAGRAM_EXCLUSIVE_KEYWORDS",
    "WEB_EXCLUSIVE_KEYWORDS",
    "WEB_INTENT_TERMS",
]
