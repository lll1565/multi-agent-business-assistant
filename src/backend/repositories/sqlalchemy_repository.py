"""SQLAlchemy session repository implementation."""

from __future__ import annotations

import json
import uuid
from backend.domain.entities import Message
from backend.domain.entities import Session as ChatSession
from backend.infrastructure.database.engine import ChatDatabase, init_schema
from backend.infrastructure.database.models import MessageModel, SessionModel
from backend.repositories.base import SessionRepository
from backend.repositories.mappers import message_to_entity, session_to_entity
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session
from typing import Any

DEFAULT_TITLE = "新对话"


class SqlAlchemySessionRepository(SessionRepository):
    """SQLAlchemy 2.0 SessionRepository implementation."""

    def __init__(self, database: ChatDatabase):
        self._db = database

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(UTC).isoformat()

    @contextmanager
    def _unit_of_work(self) -> Iterator[Session]:
        session = self._db.create_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def init_schema(self) -> None:
        init_schema(self._db)

    def create_session(self, title: str = DEFAULT_TITLE) -> ChatSession:
        session_id = str(uuid.uuid4())
        now = self._now_iso()
        row = SessionModel(
            id=session_id,
            title=title,
            created_at=now,
            updated_at=now,
        )
        with self._unit_of_work() as db:
            db.add(row)
        return session_to_entity(row)

    def list_sessions(self, limit: int = 100) -> list[ChatSession]:
        preview_subq = (
            select(MessageModel.content)
            .where(
                MessageModel.session_id == SessionModel.id,
                MessageModel.role == "user",
            )
            .order_by(MessageModel.created_at.asc())
            .limit(1)
            .scalar_subquery()
        )
        stmt = (
            select(SessionModel, preview_subq.label("preview"))
            .order_by(SessionModel.updated_at.desc())
            .limit(limit)
        )
        with self._unit_of_work() as db:
            rows = db.execute(stmt).all()
        return [session_to_entity(session, preview=preview) for session, preview in rows]

    def get_session(self, session_id: str) -> ChatSession | None:
        with self._unit_of_work() as db:
            row = db.get(SessionModel, session_id)
            if not row:
                return None
            messages = list(row.messages)
        return session_to_entity(row, messages=messages)

    def update_session_title(self, session_id: str, title: str) -> bool:
        now = self._now_iso()
        with self._unit_of_work() as db:
            result = db.execute(
                update(SessionModel)
                .where(SessionModel.id == session_id)
                .values(title=title.strip() or DEFAULT_TITLE, updated_at=now)
            )
        return (result.rowcount or 0) > 0  # type: ignore[attr-defined]

    def delete_session(self, session_id: str) -> bool:
        with self._unit_of_work() as db:
            result = db.execute(delete(SessionModel).where(SessionModel.id == session_id))
        return (result.rowcount or 0) > 0  # type: ignore[attr-defined]

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        trace: dict[str, Any] | None = None,
    ) -> Message:
        msg_id = str(uuid.uuid4())
        now = self._now_iso()
        meta = json.dumps(trace, ensure_ascii=False) if trace else None
        message = MessageModel(
            id=msg_id,
            session_id=session_id,
            role=role,
            content=content,
            created_at=now,
            meta=meta,
        )
        with self._unit_of_work() as db:
            db.add(message)
            db.execute(
                update(SessionModel).where(SessionModel.id == session_id).values(updated_at=now)
            )
        entity = message_to_entity(message)
        if trace is not None:
            entity.trace = trace
        return entity

    def auto_title_from_message(self, session_id: str, message: str) -> None:
        with self._unit_of_work() as db:
            row = db.get(SessionModel, session_id)
            if not row or row.title != DEFAULT_TITLE:
                return
            title = message.strip().replace("\n", " ")[:24]
            if len(message.strip()) > 24:
                title += "…"
            row.title = title or DEFAULT_TITLE
            row.updated_at = self._now_iso()

    def session_exists(self, session_id: str) -> bool:
        with self._unit_of_work() as db:
            return db.get(SessionModel, session_id) is not None
