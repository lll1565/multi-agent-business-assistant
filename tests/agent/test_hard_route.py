"""Tests for hard-route classification (no LLM invocation)."""

from subagent.stone.routing.hard_route import try_db_hard_route


def test_hard_route_skips_api_questions(monkeypatch):
    monkeypatch.setattr("subagent.stone.routing.hard_route.settings.enable_hard_route", True)
    assert try_db_hard_route("get_users 接口文档") is None


def test_hard_route_skips_when_disabled(monkeypatch):
    monkeypatch.setattr("subagent.stone.routing.hard_route.settings.enable_hard_route", False)
    assert try_db_hard_route("数据库里有哪些表？") is None


def test_hard_route_skips_ambiguous(monkeypatch):
    monkeypatch.setattr("subagent.stone.routing.hard_route.settings.enable_hard_route", True)
    assert try_db_hard_route("你好") is None
