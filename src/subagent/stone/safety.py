"""Declarative safety rules for prompt rendering and runtime SQL enforcement."""

from __future__ import annotations

from collections.abc import Iterable
from enum import Enum


class SafetyRule(str, Enum):
    READ_ONLY_SQL = "READ_ONLY_SQL"
    DEFAULT_ROW_LIMIT_5 = "DEFAULT_ROW_LIMIT_5"


_RULE_PROMPTS: dict[SafetyRule, str] = {
    SafetyRule.READ_ONLY_SQL: (
        "**只读 SQL**：仅允许 SELECT / WITH；禁止 INSERT / UPDATE / DELETE / "
        "DROP / ALTER / TRUNCATE / CREATE / REPLACE / ATTACH / DETACH 等。"
    ),
    SafetyRule.DEFAULT_ROW_LIMIT_5: (
        "**默认 LIMIT 5**：若用户未指定 LIMIT，自动追加 LIMIT 5，避免一次返回过多行。"
    ),
}


def format_safety_rules(rules: Iterable[SafetyRule]) -> str:
    seen: set[SafetyRule] = set()
    bullets: list[str] = []
    for rule in SafetyRule:
        if rule in rules and rule not in seen:
            bullets.append(f"- {_RULE_PROMPTS[rule]}")
            seen.add(rule)
    if not bullets:
        return ""
    return "## 安全约束\n\n" + "\n".join(bullets)


def rules_require(rules: Iterable[SafetyRule], target: SafetyRule) -> bool:
    return target in set(rules)


__all__ = [
    "SafetyRule",
    "format_safety_rules",
    "rules_require",
]
