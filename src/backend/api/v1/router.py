"""API v1 router aggregation."""

from fastapi import APIRouter

from backend.api.v1 import chat, health, sessions

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(sessions.router)
api_router.include_router(chat.router)
