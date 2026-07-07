"""Supervisor Deep Agent factory (LLM + registry-discovered subagents)."""

from __future__ import annotations

import os
from deepagents import CompiledSubAgent, create_deep_agent
from deepagents.backends import FilesystemBackend
from functools import lru_cache
from langchain_openai import ChatOpenAI
from subagent.config.logging_setup import get_logger
from subagent.config.settings import get_agent_settings
from subagent.stone.persistence.checkpointer import get_checkpointer
from subagent.stone.routing.registry import discover_stone_agents, get_registry
from subagent.stone.runtime.prompts import SUPERVISOR_EXTRA
from subagent.stone.runtime.subagent_wrapper import wrap_subagent_runnable

settings = get_agent_settings()
logger = get_logger("agent.factory")


def _base_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def _create_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        temperature=0,
    )


def _build_subagents() -> list:
    """Build CompiledSubAgent list from the registry."""
    discover_stone_agents()
    registry = get_registry()
    subagents: list = []
    for spec in registry.all():
        subagents.append(
            CompiledSubAgent(
                name=spec.name,
                description=spec.description,
                runnable=wrap_subagent_runnable(spec.factory(), spec.name),
            )
        )
    logger.info("supervisor subagents (from registry): %s", registry.names())
    return subagents


@lru_cache(maxsize=1)
def create_supervisor_agent():
    """Create main Deep Agent; subagents are discovered from the registry."""
    base_dir = _base_dir()
    llm = _create_llm()
    subagents = _build_subagents()

    return create_deep_agent(
        model=llm,
        system_prompt=SUPERVISOR_EXTRA,
        memory=[os.path.join(base_dir, "AGENTS.md")],
        subagents=subagents,
        checkpointer=get_checkpointer(),
        backend=FilesystemBackend(root_dir=base_dir, virtual_mode=True),
        name="stone_supervisor",
    )


__all__ = ["create_supervisor_agent"]
