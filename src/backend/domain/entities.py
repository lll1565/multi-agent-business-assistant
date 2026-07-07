"""Domain entities —persistence layer returns these, API layer serializes to dict."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    id: str
    role: str
    content: str
    created_at: str
    trace: dict[str, Any] | None = None


@dataclass
class Session:
    id: str
    title: str
    created_at: str
    updated_at: str
    preview: str | None = None
    messages: list[Message] = field(default_factory=list)
