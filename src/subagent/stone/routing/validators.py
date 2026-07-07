"""Input and SQL validators for the stone agent system."""

import re

FORBIDDEN_SQL_KEYWORDS = (
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "REPLACE",
    "ATTACH",
    "DETACH",
)


def validate_sql(query: str) -> tuple[bool, str]:
    """Return (ok, message). Only SELECT is allowed."""
    stripped = query.strip()
    if not stripped:
        return False, "SQL 为空"

    upper = stripped.upper()
    if not upper.startswith("SELECT") and not upper.startswith("WITH"):
        return False, "仅允许 SELECT / WITH 查询"

    for kw in FORBIDDEN_SQL_KEYWORDS:
        if re.search(rf"\b{kw}\b", upper):
            return False, f"禁止的 SQL 关键字: {kw}"

    return True, "ok"


def enforce_row_limit(query: str, default_limit: int = 5) -> str:
    """Append LIMIT when missing (matches npi_db_agent AGENTS.md)."""
    stripped = query.strip().rstrip(";")
    if re.search(r"\bLIMIT\b", stripped, re.IGNORECASE):
        return stripped
    return f"{stripped} LIMIT {default_limit}"


def validate_user_message(message: str, max_length: int = 4000) -> tuple[bool, str]:
    """Basic user input validation."""
    if not message or not message.strip():
        return False, "消息不能为空"
    if len(message) > max_length:
        return False, f"消息长度超过 {max_length} 字符"
    return True, "ok"
