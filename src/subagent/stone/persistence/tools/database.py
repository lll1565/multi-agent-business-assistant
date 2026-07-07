"""SQLite database connection (shared by npi_db_agent).

Thin wrapper over SQLAlchemy —replaces ``langchain_community.SQLDatabase``
to drop the deprecated dependency while keeping the same public surface
(``get_table_names`` / ``get_table_info`` / ``run``).
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from subagent.config.paths import resolve_demo_db_path


class SqlDb:
    """Read-oriented SQLite wrapper compatible with the small surface
    npi_db_agent uses. NOT thread-safe; create one per worker."""

    def __init__(self, db_path: str | Path, sample_rows_in_table_info: int = 3):
        path = resolve_demo_db_path(db_path)
        if not path.exists():
            raise FileNotFoundError(f"Database not found: {path}. Run: python scripts/demo_db.py")
        self._engine: Engine = create_engine(
            f"sqlite:///{path.as_posix()}",
            connect_args={"check_same_thread": False},
            future=True,
        )
        self._sample_rows = sample_rows_in_table_info

    def dispose(self) -> None:
        self._engine.dispose()

    # ----- introspection -------------------------------------------------

    def get_table_names(self) -> list[str]:
        """Return all user table names (sorted)."""
        return sorted(inspect(self._engine).get_table_names())

    def get_table_info(self, table_names: Iterable[str] | None = None) -> str:
        """Render CREATE-like statements + sample rows for the given tables
        (or all tables when ``table_names`` is None).

        Output format matches the legacy ``langchain_community.SQLDatabase``
        dialect that the supervisor prompt was tuned against:

            CREATE TABLE foo (
                id INTEGER NOT NULL,
                name VARCHAR(20),
                PRIMARY KEY (id)
            )

            /* 3 rows from foo table:
            id|name
            1|alice
            2|bob
            3|carol
            */
        """
        names = list(table_names) if table_names else self.get_table_names()
        if not names:
            return "(no tables)"

        inspector = inspect(self._engine)
        chunks: list[str] = []
        for name in names:
            chunks.append(self._format_create_table(inspector, name))
            sample = self._sample_rows_str(name)
            if sample:
                chunks.append("")
                chunks.append(f"/* {self._sample_rows} rows from {name} table:\n{sample}\n*/")
        return "\n\n".join(chunks)

    # ----- execution -----------------------------------------------------

    def run(self, query: str, include_columns: bool = True) -> str:
        """Execute a read-only SELECT and render rows as CSV-ish text.

        Matches the legacy ``SQLDatabase.run`` output: header line of
        comma-joined column names, then one row per line of comma-joined
        values (``None`` rendered as empty string).
        """
        with self._engine.connect() as conn:
            result = conn.execute(text(query))

            if result.returns_rows is False:
                # DDL/DML —but the caller is expected to validate SQL first.
                return f"{result.rowcount} rows affected."

            columns = list(result.keys()) if include_columns else []
            rows = [self._row_to_csv(row, len(columns)) for row in result.fetchall()]

        if not include_columns:
            return "\n".join(rows)
        if not rows:
            return ", ".join(columns) if columns else ""
        return ", ".join(columns) + "\n" + "\n".join(rows)

    # ----- internals -----------------------------------------------------

    def _format_create_table(self, inspector, name: str) -> str:
        cols = inspector.get_columns(name) or []
        pk = inspector.get_pk_constraint(name) or {}
        fks = inspector.get_foreign_keys(name) or []
        pk_cols = set(pk.get("constrained_columns") or [])

        lines = [f"CREATE TABLE {name} ("]
        col_lines = []
        for c in cols:
            line = f"    {c['name']} {self._format_type(c['type'])}"
            if not c.get("nullable", True):
                line += " NOT NULL"
            if c.get("default") is not None:
                line += f" DEFAULT {c['default']!r}"
            col_lines.append(line)

        if pk_cols:
            col_lines.append(f"    PRIMARY KEY ({', '.join(sorted(pk_cols))})")

        for fk in fks:
            local = ", ".join(fk.get("constrained_columns") or [])
            ref_table = fk.get("referred_table") or ""
            ref_cols = ", ".join(fk.get("referred_columns") or [])
            if local and ref_table and ref_cols:
                col_lines.append(f"    FOREIGN KEY ({local}) REFERENCES {ref_table}({ref_cols})")

        lines.append(",\n".join(col_lines))
        lines.append(")")
        return "\n".join(lines)

    @staticmethod
    def _format_type(t) -> str:
        try:
            return str(t).upper()
        except Exception:  # noqa: BLE001
            return "VARCHAR"

    def _sample_rows_str(self, name: str) -> str:
        try:
            quoted = name.replace('"', '""')
            sql = f'SELECT * FROM "{quoted}" LIMIT {self._sample_rows}'
            return self.run(sql, include_columns=True)
        except SQLAlchemyError:
            return ""

    @staticmethod
    def _row_to_csv(row, n_cols: int) -> str:
        # RowMapping / Row objects: indexable by both int and column name.
        if n_cols and len(row._mapping) != n_cols:  # type: ignore[attr-defined]
            n_cols = len(row._mapping)  # type: ignore[attr-defined]
        values = []
        for v in row:
            if v is None:
                values.append("")
            else:
                values.append(str(v).replace("\n", " ").replace("\r", " "))
        return ", ".join(values)


def get_database(db_path: str | Path | None = None) -> SqlDb:
    """Return the shared ``SqlDb`` instance for ``db_path`` (default ``demo.db``)."""
    return SqlDb(db_path or resolve_demo_db_path())


__all__ = ["SqlDb", "get_database"]
