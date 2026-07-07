"""Concrete ChatService - orchestrates persistence and agent calls."""

from __future__ import annotations

import asyncio
import json
from backend.config.logging_setup import get_logger
from backend.domain.entities import Message
from backend.ports.agent import AgentService
from backend.repositories.base import SessionRepository
from backend.repositories.mappers import message_entity_to_dict
from backend.schemas import ChatResponse
from backend.services.base import ChatService
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from typing import Any

logger = get_logger("backend.chat")

_GENERATION_FAILED = "（生成失败：{error}）"
_EMPTY_ASSISTANT = "（无内容）"


class DefaultChatService(ChatService):
    """Default chat service: sync via thread pool, stream via agent iterator."""

    def __init__(
        self,
        repo: SessionRepository,
        agent: AgentService,
        executor: ThreadPoolExecutor | None = None,
    ):
        self._repo = repo
        self._agent = agent
        self._executor = executor or ThreadPoolExecutor(max_workers=2)

    def _begin_user_turn(self, session_id: str, message: str) -> Message:
        user_msg = self._repo.add_message(session_id, "user", message)
        self._repo.auto_title_from_message(session_id, message)
        return user_msg

    def _persist_assistant_turn(
        self,
        session_id: str,
        reply: str,
        trace: dict[str, Any] | None = None,
    ) -> Message:
        return self._repo.add_message(
            session_id,
            "assistant",
            reply,
            trace=trace,
        )

    def _persist_generation_failure(self, session_id: str, error: str) -> None:
        self._persist_assistant_turn(
            session_id,
            _GENERATION_FAILED.format(error=error),
        )

    async def chat(self, session_id: str, message: str, request_id: str) -> ChatResponse:
        user_msg = self._begin_user_turn(session_id, message)

        loop = asyncio.get_running_loop()
        try:
            turn = await loop.run_in_executor(
                self._executor,
                self._agent.invoke,
                message,
                session_id,
                request_id,
            )
            reply = turn["reply"]
            trace_data = turn["trace"]
            assistant_msg = self._persist_assistant_turn(session_id, reply, trace=trace_data)
            return ChatResponse(
                reply=reply,
                success=True,
                request_id=request_id,
                trace=self.build_trace(trace_data),
                user_message=message_entity_to_dict(user_msg),
                assistant_message=message_entity_to_dict(assistant_msg),
            )
        except Exception as e:
            err_type = type(e).__name__
            logger.exception(
                "[%s] chat error session=%s type=%s",
                request_id,
                session_id,
                err_type,
            )
            self._persist_generation_failure(session_id, str(e))
            return ChatResponse(
                reply="",
                success=False,
                error=str(e),
                error_type=err_type,
                request_id=request_id,
            )

    def chat_stream(self, session_id: str, message: str, request_id: str) -> Iterator[str]:
        self._begin_user_turn(session_id, message)
        logger.info("[%s] stream chat session=%s", request_id, session_id)

        final_reply = ""
        final_trace = None
        stream_error = None
        try:
            for ev in self._agent.stream_events(message, session_id, request_id):
                yield self._sse_line(ev)
                if ev.get("type") == "done":
                    final_reply = ev.get("reply", "")
                    final_trace = ev.get("trace")
                elif ev.get("type") == "error":
                    stream_error = ev.get("error", "未知错误")
                    logger.error("[%s] stream error event: %s", request_id, stream_error)
                    break
        except Exception as exc:
            logger.exception("[%s] stream generator failed", request_id)
            stream_error = str(exc)
            yield self._sse_line(
                {
                    "type": "error",
                    "error": stream_error,
                    "error_type": type(exc).__name__,
                    "request_id": request_id,
                }
            )

        if stream_error:
            self._persist_generation_failure(session_id, stream_error)
            return

        if final_reply or final_trace:
            self._persist_assistant_turn(
                session_id,
                final_reply or _EMPTY_ASSISTANT,
                trace=final_trace,
            )
            logger.info(
                "[%s] stream saved session=%s reply_len=%d",
                request_id,
                session_id,
                len(final_reply or ""),
            )

    async def chat_legacy(self, message: str, request_id: str) -> ChatResponse:
        session = self._repo.create_session()
        return await self.chat(session.id, message, request_id)

    @staticmethod
    def _sse_line(payload: dict[str, Any]) -> str:
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
