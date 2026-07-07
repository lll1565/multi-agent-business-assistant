"""Tests for query classification and routing hints."""

import pytest

from subagent.stone.routing.classifier import (
    build_supervisor_input,
    classify_query,
    get_routing_hint,
    is_api_doc_only_query,
)


@pytest.mark.parametrize(
    "message,expected",
    [
        ("数据库里有哪些表？", "db"),
        ("查一下订单总数", "db"),
        ("get_users 接口文档", "api"),
        ("REST API 文档", "api"),
        ("对比数据库和 get_users API", "both"),
        ("你好", None),
    ],
)
def test_classify_query(message: str, expected: str | None):
    assert classify_query(message) == expected


def test_is_api_doc_only():
    assert is_api_doc_only_query("get_users 接口文档")
    assert not is_api_doc_only_query("数据库里有哪些表？")


def test_build_supervisor_input_prepends_hint():
    text = build_supervisor_input("数据库里有哪些表？")
    assert "[路由提示]" in text
    assert "npi_db_agent" in text
    assert "数据库" in text


def test_build_supervisor_input_meta_query_gets_no_delegate_hint():
    text = build_supervisor_input("你好")
    assert "[路由提示]" in text
    assert "不要委派" in text
    assert "你好" in text


def test_build_supervisor_input_plain_when_ambiguous():
    ambiguous = "随便聊点什么"
    assert build_supervisor_input(ambiguous) == ambiguous


def test_get_routing_hint_db():
    hint = get_routing_hint("查订单表")
    assert hint is not None
    assert "npi_db_agent" in hint
