from __future__ import annotations

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.infrastructure.database.base import Base


class SessionModel(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(80), nullable=False, default="新对诀")
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(64), nullable=False)

    messages: Mapped[list[MessageModel]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="MessageModel.created_at",
    )


class MessageModel(Base):
    __tablename__ = "messages"
    __table_args__ = (Index("idx_messages_session", "session_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
    meta: Mapped[str | None] = mapped_column(Text, nullable=True)

    session: Mapped[SessionModel] = relationship(back_populates="messages")
