"""Web search tools for npi_web_agent."""

from __future__ import annotations

import warnings
from langchain_core.tools import tool
from subagent.config.logging_setup import get_logger

logger = get_logger("agent.web_tools")

_MAX_RESULTS = 5


def _format_results(results: list) -> str:
    if not results:
        return "（未找到搜索结果）"
    lines = []
    for i, r in enumerate(results, 1):
        if not isinstance(r, dict):
            continue
        title = (r.get("title") or "").strip()
        url = (r.get("href") or r.get("url") or "").strip()
        snippet = (r.get("body") or r.get("snippet") or "").strip()
        lines.append(f"{i}. [{title}]({url})")
        if snippet:
            lines.append(f"   {snippet}")
    return "\n".join(lines) or "（未找到搜索结果）"


def _import_ddgs() -> tuple:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            from ddgs import DDGS  # type: ignore
        return DDGS, None
    except ImportError:
        pass
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            from duckduckgo_search import DDGS  # type: ignore
        return DDGS, None
    except ImportError:
        return None, ("DuckDuckGo 搜索包未安装。请 `pip install ddgs` 后重试。")


@tool
def search_web(query: str, max_results: int = _MAX_RESULTS) -> str:
    """Search the public web for `query`. Returns a numbered list of hits."""
    query = (query or "").strip()
    if not query:
        return "【search_web】查询不能为空"

    capped = max(1, min(int(max_results or _MAX_RESULTS), 10))
    logger.info("search_web query=%r max=%d", query, capped)

    DDGS, err = _import_ddgs()
    if DDGS is None:
        return f"【search_web】{err}"

    try:
        ddgs = DDGS()
        raw = list(ddgs.text(query, max_results=capped))
    except Exception as exc:  # noqa: BLE001
        logger.warning("search_web failed: %s: %s", type(exc).__name__, exc)
        return (
            f"【search_web】搜索失败：{type(exc).__name__}: {exc}。"
            "可能是网络受限或被限流，请换个关键词或稍后再试。"
        )

    return _format_results(raw)


def get_web_tools() -> list:
    return [search_web]
