"""Shared types for routing keyword tuples."""

from __future__ import annotations

from re import Pattern

Keyword = str | Pattern[str]

__all__ = ["Keyword"]
