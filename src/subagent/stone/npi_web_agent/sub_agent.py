"""npi_web_agent — Deep Agent for public web search."""

import os
from functools import lru_cache

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain_openai import ChatOpenAI

from subagent.config.settings import get_agent_settings

from .tools import get_web_tools

settings = get_agent_settings()


def _base_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def _create_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        temperature=0,
    )


@lru_cache(maxsize=1)
def create_npi_web_agent():
    """Create npi_web_agent with AGENTS.md and DuckDuckGo search tool."""
    base_dir = _base_dir()
    llm = _create_llm()

    return create_deep_agent(
        model=llm,
        memory=[os.path.join(base_dir, "AGENTS.md")],
        skills=[os.path.join(base_dir, "skills")],
        tools=get_web_tools(),
        subagents=[],
        backend=FilesystemBackend(root_dir=base_dir, virtual_mode=True),
        name="npi_web_agent",
    )
