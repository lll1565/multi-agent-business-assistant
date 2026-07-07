"""Public chat entrypoints (sync turn + CLI)."""

from __future__ import annotations

import argparse
import sys
from dotenv import load_dotenv
from subagent.config.logging_setup import get_logger, setup_logging
from subagent.config.settings import get_agent_settings
from subagent.stone.routing.resolve_route import RouteKind, resolve_route
from subagent.stone.runtime.turn_runner import run_supervisor_turn

load_dotenv()
settings = get_agent_settings()
logger = get_logger("agent.entrypoints")


def chat_with_trace(
    user_message: str,
    session_id: str | None = None,
    request_id: str | None = None,
) -> dict:
    """Run one turn and return reply + reasoning trace."""
    rid = request_id or "-"
    decision = resolve_route(
        user_message,
        session_id=session_id,
        request_id=rid,
    )

    if decision.kind == RouteKind.INVALID:
        return {
            "reply": f"输入无效: {decision.validation_error}",
            "trace": {"agents_used": [], "agent_labels": [], "steps": []},
        }

    if decision.result is not None:
        return decision.result

    return run_supervisor_turn(
        user_message,
        session_id=session_id,
        request_id=rid,
        routing_hint=decision.routing_hint,
    )


def chat(user_message: str, session_id: str | None = None) -> str:
    """Run one turn; session_id isolates conversation memory."""
    return chat_with_trace(user_message, session_id=session_id)["reply"]


def main() -> None:
    """CLI entry (python -m subagent.stone.runtime.core)."""
    setup_logging(
        level=settings.log_level,
        log_file=settings.log_file,
        console=settings.log_to_console,
    )
    parser = argparse.ArgumentParser(description="Stone multi-agent supervisor")
    parser.add_argument("question", nargs="*", help="User question")
    args = parser.parse_args()

    question = " ".join(args.question).strip() or "数据库里有哪些表？"
    print(f"\n问题: {question}\n")
    try:
        answer = chat(question)
        print(f"回答:\n{answer}\n")
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


__all__ = ["chat", "chat_with_trace", "main"]
