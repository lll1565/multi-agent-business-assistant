"""Fallback replies when supervisor or upstream LLM fails."""


def fallback_reply(messages: list) -> str:
    final = messages[-1] if messages else None
    if final and hasattr(final, "content"):
        return str(final.content)
    return ""


def api_doc_fallback(user_message: str, exc: Exception) -> dict | None:
    """Serve API docs without LLM when upstream model connection fails."""
    err_text = str(exc).lower()
    if "connection error" not in err_text and "timed out" not in err_text:
        return None

    from subagent.stone.routing.api_fastpath import try_api_doc_rescue

    return try_api_doc_rescue(user_message)


# Backward-compatible aliases (used by turn_runner / streaming via core re-exports)
_fallback_reply = fallback_reply
_api_doc_fallback = api_doc_fallback

__all__ = [
    "_api_doc_fallback",
    "_fallback_reply",
    "api_doc_fallback",
    "fallback_reply",
]
