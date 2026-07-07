"""Wrap sub-agent runnables: per-agent thread_id + nested trace capture."""

from __future__ import annotations

import contextvars
from langchain_core.runnables import Runnable, RunnableConfig
from subagent.config.logging_setup import get_logger
from subagent.stone.persistence.checkpointer import subagent_thread_id
from subagent.stone.runtime.trace import build_trace
from typing import Any

logger = get_logger("agent.subagent")

# Use .set(None) instead of .reset(token) —avoids ValueError when streaming
# resumes the generator in a different async context.
_nested_traces: contextvars.ContextVar[list[dict[str, Any]] | None] = contextvars.ContextVar(
    "nested_traces", default=None
)


def begin_nested_trace_capture() -> list[dict[str, Any]]:
    """Start capturing sub-agent traces for this turn. Returns the shared bucket."""
    bucket: list[dict[str, Any]] = []
    _nested_traces.set(bucket)
    return bucket


def end_nested_trace_capture(bucket: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Stop capture and return collected sub-agent traces."""
    current = _nested_traces.get()
    if bucket is not None and current is bucket:
        traces = list(bucket)
    else:
        traces = list(current or bucket or [])
    _nested_traces.set(None)
    return traces


def get_nested_traces() -> list[dict[str, Any]]:
    return list(_nested_traces.get() or [])


def _patch_config_for_subagent(config: RunnableConfig | None, agent_name: str) -> RunnableConfig:
    cfg: dict[str, Any] = dict(config or {})
    configurable = dict(cfg.get("configurable") or {})
    parent_tid = configurable.get("thread_id")
    if parent_tid:
        configurable["thread_id"] = subagent_thread_id(str(parent_tid), agent_name)
    configurable["ls_agent_type"] = "subagent"
    cfg["configurable"] = configurable
    return cfg  # type: ignore[return-value]


def _record_trace(agent_name: str, result: dict[str, Any]) -> None:
    messages = result.get("messages") or []
    if not messages:
        return
    trace = build_trace(messages)
    trace["agent"] = agent_name
    bucket = _nested_traces.get()
    if bucket is not None:
        bucket.append(trace)


class TracedSubAgentRunnable(Runnable):
    """Runnable wrapper used for CompiledSubAgent —trace + checkpoint thread."""

    def __init__(self, inner: Runnable, agent_name: str):
        self.inner = inner
        self.agent_name = agent_name

    def invoke(self, input: Any, config: RunnableConfig | None = None, **kwargs: Any) -> Any:
        cfg = _patch_config_for_subagent(config, self.agent_name)
        tid = (cfg.get("configurable") or {}).get("thread_id", "-")
        msg_preview = ""
        if isinstance(input, dict):
            msgs = input.get("messages") or []
            if msgs:
                msg_preview = str(getattr(msgs[-1], "content", ""))[:100]
        logger.info(
            "subagent invoke start agent=%s thread_id=%s preview=%r",
            self.agent_name,
            tid,
            msg_preview,
        )
        try:
            result = self.inner.invoke(input, config=cfg, **kwargs)
            if isinstance(result, dict):
                _record_trace(self.agent_name, result)
            logger.info("subagent invoke ok agent=%s thread_id=%s", self.agent_name, tid)
            return result
        except Exception as exc:
            logger.error(
                "subagent invoke FAIL agent=%s thread_id=%s type=%s err=%s",
                self.agent_name,
                tid,
                type(exc).__name__,
                exc,
            )
            raise

    async def ainvoke(self, input: Any, config: RunnableConfig | None = None, **kwargs: Any) -> Any:
        cfg = _patch_config_for_subagent(config, self.agent_name)
        tid = (cfg.get("configurable") or {}).get("thread_id", "-")
        logger.info("subagent ainvoke start agent=%s thread_id=%s", self.agent_name, tid)
        try:
            result = await self.inner.ainvoke(input, config=cfg, **kwargs)
            if isinstance(result, dict):
                _record_trace(self.agent_name, result)
            logger.info("subagent ainvoke ok agent=%s", self.agent_name)
            return result
        except Exception as exc:
            logger.error(
                "subagent ainvoke FAIL agent=%s type=%s err=%s",
                self.agent_name,
                type(exc).__name__,
                exc,
            )
            raise


def wrap_subagent_runnable(runnable: Runnable, agent_name: str) -> TracedSubAgentRunnable:
    return TracedSubAgentRunnable(runnable, agent_name)
