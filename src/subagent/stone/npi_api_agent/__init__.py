"""NPI API documentation subagent."""

import re

from subagent.stone.routing.registry import SubAgentSpec, cancel_when_db_intent
from subagent.stone.routing.routing_intents import (
    API_ENDPOINT_NAMES,
    API_EXCLUSIVE_KEYWORDS,
)

from .sub_agent import create_npi_api_agent

_API_KEYWORDS = (
    "api",
    "接口",
    "rest",
    "http",
    "endpoint",
    "路径",
    "参数",
    "请求",
    "响应",
    "文档",
    *API_ENDPOINT_NAMES,
    re.compile(r"/api/"),
)

AGENT_SPEC = SubAgentSpec(
    name="npi_api_agent",
    description="查询 REST API 文档：get_users、login 等接口的路径、参数与响应。",
    factory=create_npi_api_agent,
    keywords=_API_KEYWORDS,
    exclusive_keywords=API_EXCLUSIVE_KEYWORDS,
    exclusive_cancel_keywords=cancel_when_db_intent(),
    kind="api",
    supports_fast_path=True,
    fast_path_tools=("query_api_doc", "list_all_apis"),
    uses_persistent_checkpointer=True,
    capability_title="API 接口文档",
    capability_bullets=("查询 REST 接口路径、HTTP 方法、参数与响应示例",),
    capability_examples=(
        "get_users 接口文档",
        "有哪些接口",
    ),
    capability_order=20,
)

__all__ = ["create_npi_api_agent", "AGENT_SPEC"]
