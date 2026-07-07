"""Database engine and session factory."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from backend.infrastructure.database.base import Base


@dataclass(frozen=True)
class ChatDatabase:
    """Chat DB connection wrapper for tests and DI."""

    engine: Engine
    session_factory: sessionmaker[Session]

    def create_session(self) -> Session:
        return self.session_factory()

    def dispose(self) -> None:
        self.engine.dispose()


def create_chat_database(db_path: Path) -> ChatDatabase:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    url = f"sqlite:///{db_path.as_posix()}"
    engine = create_engine(
        url,
        connect_args={"check_same_thread": False},
        future=True,
    )
    factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    return ChatDatabase(engine=engine, session_factory=factory)


def init_schema(db: ChatDatabase) -> None:
    """Create tables; add messages.meta column for legacy DBs."""
    Base.metadata.create_all(bind=db.engine)
    inspector = inspect(db.engine)
    if "messages" in inspector.get_table_names():
        cols = {c["name"] for c in inspector.get_columns("messages")}
        if "meta" not in cols:
            with db.engine.begin() as conn:
                conn.exec_driver_sql("ALTER TABLE messages ADD COLUMN meta TEXT")
