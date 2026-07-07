"""Production security helpers — API key auth and public path rules."""

from __future__ import annotations

from fastapi import Request

_PUBLIC_PREFIXES = (
    "/api/health",
    "/api/ready",
    "/api/docs",
    "/api/redoc",
    "/api/openapi.json",
)


def is_public_path(path: str) -> bool:
    if path == "/":
        return True
    return any(path == prefix or path.startswith(f"{prefix}/") for prefix in _PUBLIC_PREFIXES)


def is_chat_mutation_path(path: str, method: str) -> bool:
    if method.upper() != "POST":
        return False
    if path == "/api/chat":
        return True
    return path.startswith("/api/sessions/") and (
        path.endswith("/chat") or path.endswith("/chat/stream")
    )


def extract_api_key(request: Request) -> str | None:
    header_key = request.headers.get("X-API-Key")
    if header_key:
        return header_key.strip()
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return None


def api_key_is_valid(request: Request, expected_key: str) -> bool:
    provided = extract_api_key(request)
    if not provided:
        return False
    return provided == expected_key


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client is not None:
        return request.client.host
    return "unknown"
