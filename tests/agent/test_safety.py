"""Tests for declarative safety rules."""

from subagent.stone.safety import SafetyRule, format_safety_rules, rules_require


def test_format_empty_returns_empty():
    assert format_safety_rules(()) == ""
    assert format_safety_rules([]) == ""


def test_format_renders_known_rules():
    text = format_safety_rules([SafetyRule.READ_ONLY_SQL, SafetyRule.DEFAULT_ROW_LIMIT_5])
    assert "## 安全约束" in text
    assert "SELECT" in text  # READ_ONLY_SQL mention
    assert "LIMIT 5" in text  # DEFAULT_ROW_LIMIT_5 mention
    assert text.count("- ") == 2


def test_format_stable_order():
    """Order in output follows enum definition, not input order."""
    a = format_safety_rules([SafetyRule.DEFAULT_ROW_LIMIT_5, SafetyRule.READ_ONLY_SQL])
    b = format_safety_rules([SafetyRule.READ_ONLY_SQL, SafetyRule.DEFAULT_ROW_LIMIT_5])
    assert a == b


def test_format_deduplicates():
    text = format_safety_rules([SafetyRule.READ_ONLY_SQL, SafetyRule.READ_ONLY_SQL])
    assert text.count("SELECT") >= 1
    assert text.count("- ") == 1


def test_rules_require_set_semantics():
    rules = [SafetyRule.READ_ONLY_SQL]
    assert rules_require(rules, SafetyRule.READ_ONLY_SQL) is True
    assert rules_require(rules, SafetyRule.DEFAULT_ROW_LIMIT_5) is False
    assert rules_require([], SafetyRule.READ_ONLY_SQL) is False


def test_db_agent_spec_declares_sql_safety():
    """The npi_db_agent spec must declare the SQL safety rules so the
    prompt and runtime enforcement stay in sync."""
    from subagent.stone.npi_db_agent import AGENT_SPEC

    assert SafetyRule.READ_ONLY_SQL in AGENT_SPEC.safety_rules
    assert SafetyRule.DEFAULT_ROW_LIMIT_5 in AGENT_SPEC.safety_rules
