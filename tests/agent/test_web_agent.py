"""Tests for the npi_web_agent (routing + tool formatting)."""

import pytest

from subagent.stone.npi_web_agent.tools import _format_results, search_web
from subagent.stone.routing.classifier import (
    classify_query,
    classify_query_agents,
    get_routing_hint,
)


@pytest.mark.parametrize(
    "message",
    [
        "搜索一下最新的 AI 新闻",
        "网上查 OpenAI 是什么",
        "今天天气怎么样",
        "为什么天空是蓝色的",
        "股价 苹果",
        "search the web for GPT-5",
        "联网搜 Python 教程",
    ],
)
def test_classify_query_agents_routes_to_web(message: str):
    agents = classify_query_agents(message)
    assert "npi_web_agent" in agents, f"expected web agent for {message!r}, got {agents}"


def test_legacy_classify_does_not_break_on_web_query():
    assert classify_query("搜索一下 Python 教程") is None


def test_db_query_not_rerouted_to_web():
    assert "npi_db_agent" in classify_query_agents("数据库里有哪些表？")
    assert "npi_web_agent" not in classify_query_agents("数据库里有哪些表？")


def test_api_query_not_rerouted_to_web():
    assert "npi_api_agent" in classify_query_agents("get_users 接口文档")
    assert "npi_web_agent" not in classify_query_agents("get_users 接口文档")


def test_generic_routing_hint_for_web():
    hint = get_routing_hint("搜索 OpenAI 是什么")
    assert hint is not None
    assert "npi_web_agent" in hint


def test_format_results_empty():
    assert _format_results([]) == "（未找到搜索结果）"


def test_format_results_single():
    out = _format_results(
        [
            {
                "title": "Hello",
                "href": "https://example.com",
                "body": "world",
            }
        ]
    )
    assert "1. [Hello](https://example.com)" in out
    assert "world" in out


def test_format_results_handles_missing_fields():
    out = _format_results([{"title": "OnlyTitle"}, {}])
    assert "OnlyTitle" in out
    assert out.startswith("1. ")


def test_search_web_empty_query():
    assert "不能为空" in search_web.invoke({"query": ""})


def test_search_web_caps_max_results():
    assert search_web.args is not None
