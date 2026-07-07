"""SubAgent registry ? pluggable multi-agent discovery.

Goal: adding a new subagent should require zero edits to `core.py` / `routing.py`.
Each `npi_*_agent` subpackage exports an `AGENT_SPEC` constant that describes
its name, description, factory, and routing keywords. `discover_stone_agents()`
walks the package, imports each subagent module, and registers its spec.

Usage (supervisor):

    from subagent.stone.routing.registry import discover_stone_agents, get_registry

    discover_stone_agents()
    for spec in get_registry().all():
        subagents.append(CompiledSubAgent(name=spec.name, ...))

Adding a new agent = create `src/subagent/stone/npi_xxx_agent/` with an
`__init__.py` that defines `AGENT_SPEC`. No other file needs to change.
"""

from __future__ import annotations

import importlib
import os
import pkgutil
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from re import Pattern
from typing import TYPE_CHECKING, Any

from subagent.config.logging_setup import get_logger
from subagent.stone.routing.routing_types import Keyword
from subagent.stone.safety import SafetyRule

if TYPE_CHECKING:
    # Imported only for type checkers / IDE hints; never at runtime so the
    # registry module stays importable in environments without langchain
    # (e.g. lightweight routing tests).
    pass

logger = get_logger("agent.registry")


@dataclass(frozen=True)
class SubAgentSpec:
    """Static metadata for one subagent.

    Attributes
    ----------
    name:
        Stable identifier used in `task` tool calls, traces, routing hints.
    description:
        Free-form description passed to `CompiledSubAgent.description` so the
        supervisor LLM knows when to delegate to this agent.
    factory:
        Zero-arg callable returning a LangChain `Runnable` (typically a
        compiled Deep Agent). Should be wrapped in `@lru_cache` so repeated
        `create_*_agent()` calls reuse the same instance.
    keywords:
        Intent signals used by the lightweight classifier. Matched with
        `re.search` (case-insensitive for strings, as-authored for patterns).
    exclusive_keywords:
        Strong intent signals that, when matched, force routing to this
        agent. Cancelled by `exclusive_cancel_keywords` (see below).
    exclusive_cancel_keywords:
        Subset of *other* agents' intent vocabulary that suppresses this
        agent's `exclusive_keywords` override. E.g. the API agent's
        exclusive "????" is cancelled when DB terms like "???" or
        "demo.db" also appear, preserving the legacy "force API only when
        no DB intent" behavior.
    kind:
        Free-form category tag. The legacy classifier maps ``"db"`` and
        ``"api"`` to the historical ``"db"``/``"api"``/``"both"`` outputs;
        new kinds are reported via the agent's name in routing hints.
    supports_hard_route:
        Hint that this agent can be invoked directly by the deterministic
        router (skipping the supervisor LLM) when classification is
        unambiguous. Implemented in `hard_route.py`.
    supports_fast_path:
        Hint that this agent has a zero-LLM lookup path. Implemented in
        `*_fastpath.py` modules. When true, ``fast_path_tools`` must list
        tool function names exported from ``{name}.tools``.
    fast_path_tools:
        Names of LangChain tools (in ``subagent.stone.{name}.tools``) used by
        the API fast path. Convention: ``(query_tool, list_all_tool?)``.
    uses_persistent_checkpointer:
        When true, session deletion must purge ``{session_id}::{name}``
        checkpoint threads for this agent.
    capability_title:
        User-facing section title in meta fast-path replies (e.g. "数据库查询").
        Falls back to a title derived from ``kind`` when empty.
    capability_bullets:
        Bullet points shown under ``capability_title`` in help/capability replies.
        Falls back to the first sentence of ``description`` when empty.
    capability_examples:
        Example user queries shown in help/capability replies.
    capability_order:
        Sort order when listing capabilities (lower first).
    safety_rules:
        Declarative safety constraints (see ``subagent.stone.safety``).
        Both the agent's system prompt and runtime tool wrappers consume
        this tuple, so adding a rule here propagates to both sides.
    """

    name: str
    description: str
    factory: Callable[[], Any]
    keywords: tuple[Keyword, ...] = ()
    exclusive_keywords: tuple[Keyword, ...] = ()
    exclusive_cancel_keywords: tuple[Keyword, ...] = ()
    kind: str = "generic"
    supports_hard_route: bool = False
    supports_fast_path: bool = False
    fast_path_tools: tuple[str, ...] = ()
    uses_persistent_checkpointer: bool = False
    capability_title: str = ""
    capability_bullets: tuple[str, ...] = ()
    capability_examples: tuple[str, ...] = ()
    capability_order: int = 100
    safety_rules: tuple[SafetyRule, ...] = ()


class SubAgentRegistry:
    """In-memory registry of subagent specs. Idempotent and thread-unsafe
    (registration only happens at import / startup, never in hot paths)."""

    def __init__(self) -> None:
        self._specs: dict[str, SubAgentSpec] = {}
        self._discovered: bool = False

    def register(self, spec: SubAgentSpec) -> None:
        if not isinstance(spec, SubAgentSpec):
            raise TypeError(f"expected SubAgentSpec, got {type(spec).__name__}")
        if spec.name in self._specs:
            raise ValueError(f"subagent already registered: {spec.name!r}")
        if not spec.name:
            raise ValueError("subagent name must be non-empty")
        self._specs[spec.name] = spec

    def get(self, name: str) -> SubAgentSpec | None:
        return self._specs.get(name)

    def all(self) -> tuple[SubAgentSpec, ...]:
        return tuple(self._specs.values())

    def names(self) -> tuple[str, ...]:
        return tuple(self._specs.keys())

    def clear(self) -> None:
        self._specs.clear()
        self._discovered = False

    @property
    def discovered(self) -> bool:
        return self._discovered

    def mark_discovered(self) -> None:
        self._discovered = True


_REGISTRY = SubAgentRegistry()


def get_registry() -> SubAgentRegistry:
    return _REGISTRY


def reset_registry() -> None:
    """Test helper ? drop all registered specs and discovery state."""
    _REGISTRY.clear()
    try:
        from subagent.stone.routing.api_fastpath import clear_fast_path_cache

        clear_fast_path_cache()
    except ImportError:
        pass


def discover_stone_agents() -> SubAgentRegistry:
    """Import every `npi_*_agent` subpackage and register its `AGENT_SPEC`.

    Idempotent: subsequent calls are no-ops once discovery has run.
    Safe to call from any module that needs the registry populated.

    Failures during individual subagent import are caught and logged
    so a single broken agent does not take down the supervisor.
    """
    if _REGISTRY.discovered:
        return _REGISTRY

    import subagent.stone as stone_pkg

    stone_dir = os.path.dirname(stone_pkg.__file__) or "."
    discovered_count = 0
    for mod_info in pkgutil.iter_modules([stone_dir]):
        name = mod_info.name
        if not (name.startswith("npi_") and name.endswith("_agent")):
            continue
        full_name = f"subagent.stone.{name}"
        try:
            mod = importlib.import_module(full_name)
        except Exception as exc:  # noqa: BLE001
            logger.warning("discover: skip %s (%s: %s)", name, type(exc).__name__, exc)
            continue
        spec = getattr(mod, "AGENT_SPEC", None)
        if spec is None:
            logger.debug("discover: %s has no AGENT_SPEC, skipping", name)
            continue
        if not isinstance(spec, SubAgentSpec):
            logger.warning(
                "discover: %s.AGENT_SPEC is %s, expected SubAgentSpec - skipping",
                name,
                type(spec).__name__,
            )
            continue
        if spec.name in _REGISTRY._specs:
            logger.warning("discover: %r already registered, skipping", spec.name)
            continue
        _REGISTRY.register(spec)
        discovered_count += 1
        logger.info("discover: registered %s (kind=%s)", spec.name, spec.kind)

    _REGISTRY.mark_discovered()
    logger.info("discover: %d subagent(s) registered", discovered_count)
    return _REGISTRY


# ---------------------------------------------------------------------------
# Keyword matching helpers
# ---------------------------------------------------------------------------


def _compile_keyword(kw: Keyword) -> Pattern[str]:
    """Turn a `Keyword` into a compiled `re.Pattern`."""
    if isinstance(kw, Pattern):
        return kw
    return re.compile(re.escape(kw), re.IGNORECASE)


def keyword_matches(kw: Keyword, text: str) -> bool:
    """Return True iff `kw` matches anywhere in `text`."""
    return bool(_compile_keyword(kw).search(text))


def any_keyword_matches(keywords: Iterable[Keyword], text: str) -> bool:
    """Short-circuiting OR over a keyword iterable."""
    for kw in keywords:
        if keyword_matches(kw, text):
            return True
    return False


def cancel_when_db_intent() -> tuple[Keyword, ...]:
    """Terms that suppress exclusive routing when DB intent is present."""
    from subagent.stone.routing.routing_intents import CANCEL_WHEN_DB_INTENT

    return CANCEL_WHEN_DB_INTENT


def cancel_when_db_or_api_intent() -> tuple[Keyword, ...]:
    """Terms that suppress web exclusive routing when DB or API intent appears."""
    from subagent.stone.routing.routing_intents import CANCEL_WHEN_DB_OR_API_INTENT

    return CANCEL_WHEN_DB_OR_API_INTENT


def cancel_when_not_diagram() -> tuple[Keyword, ...]:
    """Strong non-diagram signals (curated db / api / web anchors)."""
    from subagent.stone.routing.routing_intents import CANCEL_WHEN_NOT_DIAGRAM

    return CANCEL_WHEN_NOT_DIAGRAM


def aggregated_keywords_for_kinds(registry: SubAgentRegistry, *kinds: str) -> tuple[Keyword, ...]:
    """Union of ``keywords`` from specs whose ``kind`` is listed (deduplicated)."""
    seen: set[str | int] = set()
    out: list[Keyword] = []
    for spec in registry.all():
        if spec.kind not in kinds:
            continue
        for kw in spec.keywords:
            key: str | int = kw.pattern if isinstance(kw, Pattern) else kw.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(kw)
    return tuple(out)


__all__ = [
    "Keyword",
    "SubAgentSpec",
    "SubAgentRegistry",
    "aggregated_keywords_for_kinds",
    "any_keyword_matches",
    "cancel_when_db_intent",
    "cancel_when_db_or_api_intent",
    "cancel_when_not_diagram",
    "discover_stone_agents",
    "get_registry",
    "keyword_matches",
    "reset_registry",
]
