"""ORM / entity to API dict mappers."""

from __future__ import annotations

import json
from typing import Any

from backend.domain.entities import Message, Session
from backend.infrastructure.database.models import MessageModel, SessionModel


def message_to_entity(row: MessageModel) -> Message:
    trace = None
    if row.meta:
        try:
            trace = json.loads(row.meta)
        except json.JSONDecodeError:
            trace = None
    return Message(
        id=row.id,
        role=row.role,
        content=row.content,
        created_at=row.created_at,
        trace=trace,
    )


def session_to_entity(
    row: SessionModel,
    *,
    messages: list[MessageModel] | None = None,
    preview: str | None = None,
) -> Session:
    msg_entities = [message_to_entity(m) for m in messages] if messages is not None else []
    return Session(
        id=row.id,
        title=row.title,
        created_at=row.created_at,
        updated_at=row.updated_at,
        preview=preview,
        messages=msg_entities,
    )


def message_entity_to_dict(msg: Message) -> dict[str, Any]:
    out: dict[str, Any] = {
        "id": msg.id,
        "role": msg.role,
        "content": msg.content,
        "created_at": msg.created_at,
    }
    if msg.trace is not None:
        out["trace"] = msg.trace
    return out


def session_entity_to_dict(sess: Session, *, include_messages: bool = True) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": sess.id,
        "title": sess.title,
        "created_at": sess.created_at,
        "updated_at": sess.updated_at,
    }
    if sess.preview is not None:
        data["preview"] = sess.preview
    if include_messages:
        data["messages"] = [message_entity_to_dict(m) for m in sess.messages]
    return data


# Backward-compatible aliases used by older imports
message_to_dict = message_entity_to_dict


def session_to_dict(
    row: SessionModel,
    *,
    messages: list[MessageModel] | None = None,
    preview: str | None = None,
) -> dict[str, Any]:
    entity = session_to_entity(row, messages=messages, preview=preview)
    return session_entity_to_dict(entity)
