"""Golden agent classification eval —keyword routing regression."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from subagent.stone.routing.classifier import classify_query_agents

_GOLDEN_FILE = Path(__file__).parent / "golden_agent_eval.yaml"


def _load_cases() -> list[dict]:
    with _GOLDEN_FILE.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data["cases"]


@pytest.mark.parametrize("case", _load_cases(), ids=lambda c: c["message"])
def test_golden_agent_classification(case: dict):
    expected = sorted(case["agents"])
    actual = sorted(classify_query_agents(case["message"]))
    assert actual == expected
