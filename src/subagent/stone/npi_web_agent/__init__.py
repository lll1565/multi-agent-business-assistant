"""NPI web search subagent (DuckDuckGo)."""

import re
from subagent.stone.routing.registry import SubAgentSpec, cancel_when_db_or_api_intent
from subagent.stone.routing.routing_intents import WEB_EXCLUSIVE_KEYWORDS

from .sub_agent import create_npi_web_agent

_WEB_KEYWORDS = (
    "搜索",
    "搜一下",
    "网上",
    "联网",
    "天气",
    "新闻",
    "股价",
    "为什么",
    "热搜",
    "百度",
    "谷歌",
    "查询网上",
    "联网搜",
    "上网查",
    "在线查",
    "查网上",
    "互联网",
    "search",
    "web",
    "internet",
    "online",
    "look up",
    "google",
    "bing",
    re.compile(r"联\s*网"),
    re.compile(r"搜\s*索"),
)

AGENT_SPEC = SubAgentSpec(
    name="npi_web_agent",
    description=(
        "用 DuckDuckGo 搜索公开网页信息（新闻/百科/教程等）。"
        "适合实时资讯、公开知识；本地 demo.db 与 API 文档请用对应 Agent。"
    ),
    factory=create_npi_web_agent,
    keywords=_WEB_KEYWORDS,
    exclusive_keywords=WEB_EXCLUSIVE_KEYWORDS,
    exclusive_cancel_keywords=cancel_when_db_or_api_intent(),
    kind="web",
    supports_hard_route=False,
    capability_title="网页搜索",
    capability_bullets=(
        "搜索公开网页信息（新闻、百科、教程等）",
        "适合实时资讯与公开知识，不查本地业务库",
    ),
    capability_examples=(
        "搜一下 LangGraph 是什么",
        "联网查今天的新闻",
    ),
    capability_order=30,
)

__all__ = ["create_npi_web_agent", "AGENT_SPEC"]
