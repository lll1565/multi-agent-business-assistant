"""Tests for SQL and input validators."""

import pytest

from subagent.stone.routing.validators import enforce_row_limit, validate_sql, validate_user_message


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM products",
        "WITH cte AS (SELECT 1) SELECT * FROM cte",
    ],
)
def test_validate_sql_allows_select(sql: str):
    ok, msg = validate_sql(sql)
    assert ok, msg


@pytest.mark.parametrize(
    "sql",
    [
        "",
        "INSERT INTO products VALUES (1)",
        "DROP TABLE products",
        "DELETE FROM orders",
    ],
)
def test_validate_sql_rejects_unsafe(sql: str):
    ok, _ = validate_sql(sql)
    assert not ok


def test_enforce_row_limit_appends():
    assert enforce_row_limit("SELECT 1") == "SELECT 1 LIMIT 5"


def test_enforce_row_limit_skips_when_present():
    q = "SELECT 1 LIMIT 10"
    assert enforce_row_limit(q) == q


def test_validate_user_message_empty():
    ok, err = validate_user_message("   ")
    assert not ok
    assert "空" in err


def test_validate_user_message_too_long():
    ok, err = validate_user_message("x" * 5000)
    assert not ok
    assert "4000" in err
