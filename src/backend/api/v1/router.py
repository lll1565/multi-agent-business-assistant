"""API v1 router aggregation."""

from backend.api.v1 import chat, health, sessions
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(sessions.router)
api_router.include_router(chat.router)
