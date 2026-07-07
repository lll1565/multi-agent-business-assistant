"""npi_db_agent —Deep Agent for text-to-SQL (aligned with deepagents example)."""

import os
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from functools import lru_cache
from langchain_openai import ChatOpenAI
from pathlib import Path
from subagent.config.settings import get_agent_settings

settings = get_agent_settings()
from subagent.stone.persistence.tools import get_sql_tools
from subagent.stone.safety import format_safety_rules


def _base_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def _create_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        temperature=0,
    )


def _build_system_prompt(base_dir: str, safety_rules) -> str:
    """Load ``AGENTS.md`` and append the formatted safety section so the
    declarative ``AGENT_SPEC.safety_rules`` flows into the prompt without
    duplicating prose in markdown."""
    agents_md = Path(base_dir) / "AGENTS.md"
    base = agents_md.read_text(encoding="utf-8") if agents_md.exists() else ""
    safety = format_safety_rules(safety_rules)
    if safety:
        return f"{base.rstrip()}\n\n{safety}" if base else safety
    return base


@lru_cache(maxsize=1)
def create_npi_db_agent():
    """Create npi_db_agent with AGENTS.md, skills/, and shared SQL tools."""
    # Deferred import: AGENT_SPEC lives in this package's __init__, which
    # imports from this module —circular otherwise.
    from . import AGENT_SPEC

    base_dir = _base_dir()
    llm = _create_llm()
    sql_tools = get_sql_tools(
        llm,
        db_path=settings.db_path,
        safety_rules=AGENT_SPEC.safety_rules,
    )

    return create_deep_agent(
        model=llm,
        system_prompt=_build_system_prompt(base_dir, AGENT_SPEC.safety_rules),
        skills=[os.path.join(base_dir, "skills")],
        tools=sql_tools,
        subagents=[],
        backend=FilesystemBackend(root_dir=base_dir, virtual_mode=True),
        name="npi_db_agent",
    )
