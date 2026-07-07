"""npi_diagram_agent — Deep Agent that turns text into Graphviz diagrams."""

import os
from functools import lru_cache

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain_openai import ChatOpenAI

from subagent.config.settings import get_agent_settings

from .tools import get_diagram_tools

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
def create_npi_diagram_agent():
    """Create npi_diagram_agent with AGENTS.md, DOT skill, render_diagram tool."""
    base_dir = _base_dir()
    llm = _create_llm()

    return create_deep_agent(
        model=llm,
        memory=[os.path.join(base_dir, "AGENTS.md")],
        skills=[os.path.join(base_dir, "skills")],
        tools=get_diagram_tools(),
        subagents=[],
        backend=FilesystemBackend(root_dir=base_dir, virtual_mode=True),
        name="npi_diagram_agent",
    )
