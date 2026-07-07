"""SQL toolkit — sql_db_list_tables, sql_db_schema, sql_db_query.

Drops the deprecated ``langchain_community.agent_toolkits.SQLDatabaseToolkit``
in favor of three hand-rolled ``StructuredTool`` instances over the
SQLAlchemy-based ``SqlDb``.

Safety enforcement is driven by ``safety_rules`` (see ``subagent.stone.safety``)
so the same declarative source feeds both the agent's prompt and runtime
SQL validation.
"""

from __future__ import annotations

from collections.abc import Iterable

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel, Field

from subagent.config.settings import get_agent_settings
from subagent.stone.routing.validators import enforce_row_limit, validate_sql
from subagent.stone.safety import SafetyRule, rules_require

from .database import SqlDb, get_database

settings = get_agent_settings()

# ---------------------------------------------------------------------------
# Tool input schemas
# ---------------------------------------------------------------------------


class _SchemaInput(BaseModel):
    table_names: str | None = Field(
        default=None,
        description=(
            "Comma-separated list of table names to inspect. Leave empty to inspect every table."
        ),
    )


class _QueryInput(BaseModel):
    query: str = Field(description="A read-only SQL SELECT / WITH statement.")


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def _wrap_sql_query_tool(raw_tool: BaseTool, safety_rules: Iterable[SafetyRule] = ()) -> BaseTool:
    """Enforce ``safety_rules`` before delegating to ``raw_tool``.

    Active rules:

    - ``READ_ONLY_SQL`` — reject non-SELECT/WITH statements and any
      statement containing a forbidden keyword.
    - ``DEFAULT_ROW_LIMIT_5`` — append ``LIMIT 5`` when the query has
      no explicit ``LIMIT`` clause.
    """

    rule_set = set(safety_rules)
    want_read_only = rules_require(rule_set, SafetyRule.READ_ONLY_SQL)
    want_row_limit = rules_require(rule_set, SafetyRule.DEFAULT_ROW_LIMIT_5)

    def _safe_query(query: str) -> str:
        if want_read_only:
            ok, msg = validate_sql(query)
            if not ok:
                return f"【SQL 校验失败】{msg}。仅允许 SELECT / WITH 只读查询。"
        safe = enforce_row_limit(query) if want_row_limit else query
        return raw_tool.invoke({"query": safe})

    description = (raw_tool.description or "").strip()
    extras: list[str] = []
    if want_read_only:
        extras.append("只读 SQL")
    if want_row_limit:
        extras.append("无 LIMIT 时默认 LIMIT 5")
    extra = ("（" + "；".join(extras) + "）") if extras else ""
    return StructuredTool.from_function(
        name=raw_tool.name,
        description=description + extra,
        func=_safe_query,
        args_schema=_QueryInput,
    )


def _build_list_tables_tool(db: SqlDb) -> BaseTool:
    def _list_tables() -> str:
        names = db.get_table_names()
        return ", ".join(names) if names else "(no tables)"

    return StructuredTool.from_function(
        name="sql_db_list_tables",
        description=(
            "List all table names available in the connected SQLite database. "
            "Use this to discover current tables before writing SQL."
        ),
        func=_list_tables,
    )


def _build_schema_tool(db: SqlDb) -> BaseTool:
    def _schema(table_names: str | None = None) -> str:
        names = None
        if table_names:
            names = [t.strip() for t in table_names.split(",") if t.strip()]
        info = db.get_table_info(names)
        return info or "(no schema)"

    return StructuredTool.from_function(
        name="sql_db_schema",
        description=(
            "Get the schema (CREATE TABLE + sample rows) for the specified "
            "tables. Pass comma-separated table names, or omit to inspect "
            "every table."
        ),
        func=_schema,
        args_schema=_SchemaInput,
    )


def _build_query_tool(db: SqlDb) -> BaseTool:
    def _query(query: str) -> str:
        return db.run(query)

    return StructuredTool.from_function(
        name="sql_db_query",
        description="Execute a SQL query against the connected database and return rows.",
        func=_query,
        args_schema=_QueryInput,
    )


def get_sql_tools(
    llm: BaseChatModel,
    db_path: str | None = None,
    safety_rules: Iterable[SafetyRule] = (),
) -> list[BaseTool]:
    """Build the three SQL tools over the configured database.

    ``llm`` is accepted only to preserve the legacy signature; the
    SQL toolkit is deterministic and does not need the LLM.
    ``safety_rules`` drives runtime enforcement on the query tool.
    """
    del llm  # noqa: F841 — kept for backward-compatible signature
    db: SqlDb = get_database(db_path or settings.db_path)
    raw_query = _build_query_tool(db)
    return [
        _build_list_tables_tool(db),
        _build_schema_tool(db),
        _wrap_sql_query_tool(raw_query, safety_rules),
    ]


__all__ = ["get_sql_tools"]
