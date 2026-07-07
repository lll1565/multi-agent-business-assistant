"""Golden route regression tests —loaded from tests/golden_routes.yaml."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from subagent.stone.routing.resolve_route import RouteKind, resolve_route_kind

_GOLDEN_FILE = Path(__file__).parent / "golden_routes.yaml"


def _load_cases() -> list[dict]:
    with _GOLDEN_FILE.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data["cases"]


@pytest.mark.parametrize("case", _load_cases(), ids=lambda c: c["message"] or "(empty)")
def test_golden_route_kind(case: dict):
    expected = RouteKind(case["route"])
    assert resolve_route_kind(case["message"]) == expected
