"""Contract tests for shared routing vocabulary (single source of truth)."""

from subagent.stone.npi_api_agent import AGENT_SPEC as API_SPEC
from subagent.stone.npi_db_agent import AGENT_SPEC as DB_SPEC
from subagent.stone.npi_diagram_agent import AGENT_SPEC as DIAGRAM_SPEC
from subagent.stone.npi_web_agent import AGENT_SPEC as WEB_SPEC
from subagent.stone.routing.registry import (
    cancel_when_db_intent,
    cancel_when_db_or_api_intent,
    cancel_when_not_diagram,
)
from subagent.stone.routing.routing_intents import (
    API_ENDPOINT_NAMES,
    API_ENDPOINT_NAMES_EXCLUSIVE,
    API_EXCLUSIVE_KEYWORDS,
    API_LIST_ALL_QUERY_PATTERN,
    CANCEL_WHEN_DB_INTENT,
    CANCEL_WHEN_DB_OR_API_INTENT,
    CANCEL_WHEN_NOT_DIAGRAM,
    DB_TABLE_NAMES,
    DIAGRAM_EXCLUSIVE_KEYWORDS,
    WEB_EXCLUSIVE_KEYWORDS,
)


def _keyword_strings(keywords: tuple) -> set[str]:
    out: set[str] = set()
    for kw in keywords:
        if hasattr(kw, "pattern"):
            out.add(kw.pattern.lower())
        else:
            out.add(str(kw).lower())
    return out


def test_api_endpoint_names_exclusive_is_documented_subset():
    assert API_ENDPOINT_NAMES_EXCLUSIVE == ("get_users", "get_user", "create_user")
    assert set(API_ENDPOINT_NAMES_EXCLUSIVE) <= set(API_ENDPOINT_NAMES)
    for name in API_ENDPOINT_NAMES_EXCLUSIVE:
        assert name in API_EXCLUSIVE_KEYWORDS


def test_agent_specs_use_routing_intents_exclusive_tuples():
    assert API_SPEC.exclusive_keywords is API_EXCLUSIVE_KEYWORDS
    assert WEB_SPEC.exclusive_keywords is WEB_EXCLUSIVE_KEYWORDS
    assert DIAGRAM_SPEC.exclusive_keywords is DIAGRAM_EXCLUSIVE_KEYWORDS


def test_cancel_helpers_delegate_to_routing_intents():
    assert cancel_when_db_intent() is CANCEL_WHEN_DB_INTENT
    assert cancel_when_db_or_api_intent() is CANCEL_WHEN_DB_OR_API_INTENT
    assert cancel_when_not_diagram() is CANCEL_WHEN_NOT_DIAGRAM


def test_db_table_names_propagate_to_db_agent_keywords():
    db_blob = _keyword_strings(DB_SPEC.keywords)
    for table in DB_TABLE_NAMES:
        assert table.lower() in db_blob


def test_api_list_all_query_pattern_matches_list_intent():
    assert API_LIST_ALL_QUERY_PATTERN.search("\u6709\u54ea\u4e9b\u63a5\u53e3")
    assert not API_LIST_ALL_QUERY_PATTERN.search("get_users \u63a5\u53e3\u6587\u6863")


def test_api_endpoint_names_in_web_cancel_list():
    cancel_terms = _keyword_strings(WEB_SPEC.exclusive_cancel_keywords)
    for name in ("get_users", "get_user", "login"):
        assert name in API_ENDPOINT_NAMES
        assert name.lower() in cancel_terms
