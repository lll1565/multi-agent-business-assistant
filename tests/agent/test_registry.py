"""Tests for the SubAgent registry."""

import pytest

from subagent.stone.routing.registry import (
    SubAgentRegistry,
    SubAgentSpec,
    any_keyword_matches,
    discover_stone_agents,
    get_registry,
    keyword_matches,
    reset_registry,
)


def _dummy_factory():
    class _Noop:
        def invoke(self, *args, **kwargs):
            return {"messages": []}

    return _Noop()


@pytest.fixture(autouse=True)
def _clean_registry():
    reset_registry()
    yield
    reset_registry()


def test_register_and_get():
    reg = SubAgentRegistry()
    spec = SubAgentSpec(
        name="npi_test_agent",
        description="test",
        factory=_dummy_factory,
    )
    reg.register(spec)
    assert reg.get("npi_test_agent") is spec
    assert reg.names() == ("npi_test_agent",)
    assert reg.all() == (spec,)
    assert reg.discovered is False


def test_register_rejects_duplicate():
    reg = SubAgentRegistry()
    spec = SubAgentSpec(name="dup", description="x", factory=_dummy_factory)
    reg.register(spec)
    with pytest.raises(ValueError, match="already registered"):
        reg.register(spec)


def test_register_rejects_empty_name():
    reg = SubAgentRegistry()
    spec = SubAgentSpec(name="", description="x", factory=_dummy_factory)
    with pytest.raises(ValueError, match="non-empty"):
        reg.register(spec)


def test_register_rejects_non_spec():
    reg = SubAgentRegistry()
    with pytest.raises(TypeError):
        reg.register("not a spec")  # type: ignore[arg-type]


def test_clear_resets_discovered_flag():
    reg = SubAgentRegistry()
    reg.register(SubAgentSpec(name="a", description="x", factory=_dummy_factory))
    reg.mark_discovered()
    reg.clear()
    assert reg.discovered is False
    assert reg.names() == ()


def test_keyword_matches_string_substring_case_insensitive():
    assert keyword_matches("Database", "where is the database?")
    assert keyword_matches("数据库", "数据库里有哪些表？")
    assert not keyword_matches("订单", "客户列表")


def test_keyword_matches_pattern():
    import re

    pat = re.compile(r"列出.*表")
    assert keyword_matches(pat, "列出所有表")
    assert not keyword_matches(pat, "没有相关词")


def test_any_keyword_matches_short_circuits():
    kws = ("a", "b", "c")
    assert any_keyword_matches(kws, "the letter b appears")
    assert not any_keyword_matches(kws, "nothing here")
    assert not any_keyword_matches((), "anything")


def test_discover_finds_all_agents():
    discover_stone_agents()
    reg = get_registry()
    names = set(reg.names())
    assert "npi_db_agent" in names
    assert "npi_api_agent" in names
    assert "npi_web_agent" in names
    assert "npi_diagram_agent" in names
    assert reg.discovered is True


def test_discover_is_idempotent():
    discover_stone_agents()
    first = set(get_registry().names())
    discover_stone_agents()
    second = set(get_registry().names())
    assert first == second


def test_discovered_agents_have_required_metadata():
    discover_stone_agents()
    for spec in get_registry().all():
        assert spec.name.startswith("npi_")
        assert spec.description
        assert callable(spec.factory)
        assert spec.keywords
        assert isinstance(spec.kind, str) and spec.kind


def test_db_agent_kind_is_db():
    discover_stone_agents()
    spec = get_registry().get("npi_db_agent")
    assert spec is not None
    assert spec.kind == "db"
    assert spec.supports_hard_route is True
    assert spec.uses_persistent_checkpointer is True


def test_api_agent_kind_is_api():
    discover_stone_agents()
    spec = get_registry().get("npi_api_agent")
    assert spec is not None
    assert spec.kind == "api"
    assert spec.supports_fast_path is True
    assert spec.fast_path_tools == ("query_api_doc", "list_all_apis")
    assert spec.uses_persistent_checkpointer is True
    assert spec.exclusive_keywords


def test_web_agent_kind_is_web():
    discover_stone_agents()
    spec = get_registry().get("npi_web_agent")
    assert spec is not None
    assert spec.kind == "web"
    assert spec.uses_persistent_checkpointer is False
    assert spec.exclusive_keywords


def test_diagram_agent_kind_is_diagram():
    discover_stone_agents()
    spec = get_registry().get("npi_diagram_agent")
    assert spec is not None
    assert spec.kind == "diagram"
    assert spec.exclusive_keywords
    assert spec.exclusive_cancel_keywords
