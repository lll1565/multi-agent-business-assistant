"""FastAPI application factory."""

import logging
import os
from backend.api.deps import get_request_id
from backend.api.v1.router import api_router
from backend.app.container import build_container
from backend.app.middleware import request_logging_middleware, security_middleware
from backend.app.static_files import mount_frontend
from backend.config.logging_setup import get_logger, setup_logging
from backend.config.paths import resolve_project_root
from backend.config.settings import get_backend_settings
from backend.config.structured_log import log_event
from backend.config.tracing import configure_tracing, shutdown_tracing
from backend.core.exceptions import register_exception_handlers
from backend.core.response import ApiResponse, ok
from backend.schemas import RootData
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from subagent.config.paths import resolve_checkpoint_db_path
from subagent.config.settings import get_agent_settings

logger = get_logger("backend.api")

OPENAPI_TAGS = [
    {
        "name": "健康",
        "description": "健康检查与服务元信息",
    },
    {
        "name": "会话",
        "description": "ChatGPT 风格会话 CRUD",
    },
    {
        "name": "聊天",
        "description": "同步聊天与 SSE 流式",
    },
]


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    agent_settings = get_agent_settings()
    backend_settings = get_backend_settings()
    tracing_flags = configure_tracing(backend_settings)
    key_ok = bool(agent_settings.openai_api_key and agent_settings.openai_api_key.strip())
    log_event(
        logger,
        logging.INFO,
        "backend_startup",
        model=agent_settings.openai_model,
        base_url=agent_settings.openai_base_url,
        api_key_set=key_ok,
        log_file=backend_settings.log_file,
        langsmith=tracing_flags["langsmith"],
        otel=tracing_flags["otel"],
    )
    if not key_ok:
        logger.warning("OPENAI_API_KEY 未配置，Agent 调用 LLM 将失败")

    workers = os.environ.get("UVICORN_WORKERS") or os.environ.get("WEB_CONCURRENCY")
    worker_count = str(workers).strip() if workers is not None else ""
    if worker_count and worker_count not in ("1",):
        raise RuntimeError(
            f"不支持 UVICORN_WORKERS/WEB_CONCURRENCY={worker_count!r}："
            "Agent checkpoint 使用共享 SQLite，请保持 workers=1；"
            "多 worker 需迁移到 Postgres checkpoint。"
        )

    logger.info(
        "Agent checkpoint: ? worker ???LangGraph ??? %s",
        resolve_checkpoint_db_path(),
    )

    yield

    db = getattr(app.state.container, "database", None)
    if db is not None and hasattr(db, "dispose"):
        db.dispose()
        logger.info("database engine disposed")
    shutdown_tracing()


def create_app() -> FastAPI:
    backend_settings = get_backend_settings()
    setup_logging(
        level=backend_settings.log_level,
        log_file=backend_settings.log_file,
        console=backend_settings.log_to_console,
        log_format=backend_settings.log_format,
    )

    app = FastAPI(
        title="Multi-Agent Chat API",
        version="2.2.0",
        description=(
            "多 Agent + 子 Agent（NPI 数据库 / API 文档 / 联网 / 图表）聊天后端。\n\n"
            "**Swagger UI**: [/api/docs](/api/docs)  \n"
            "**ReDoc**: [/api/redoc](/api/redoc)  \n"
            "**OpenAPI JSON**: [/api/openapi.json](/api/openapi.json)"
        ),
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        openapi_tags=OPENAPI_TAGS,
        lifespan=_lifespan,
    )

    app.state.container = build_container()

    register_exception_handlers(app)

    trusted_hosts = backend_settings.trusted_host_list
    if trusted_hosts:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=backend_settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.middleware("http")(security_middleware)
    app.middleware("http")(request_logging_middleware)

    app.include_router(api_router, prefix="/api")

    if backend_settings.serve_frontend:
        dist_dir = resolve_project_root() / backend_settings.frontend_dist_path
        mount_frontend(app, dist_dir)

    @app.get("/", include_in_schema=False, response_model=ApiResponse[RootData])
    def root_redirect(request_id: str = Depends(get_request_id)) -> ApiResponse[RootData]:
        return ok(
            RootData(message="Multi-Agent Chat API"),
            request_id=request_id,
        )

    return app
