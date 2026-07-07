"""Health check endpoints."""

from backend.api.deps import get_request_id
from backend.config.paths import resolve_project_root
from backend.config.settings import get_backend_settings
from backend.core.response import ApiResponse, ok
from backend.schemas import HealthResponse, ReadyCheck, ReadyResponse
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from subagent.config.paths import resolve_checkpoint_db_path
from subagent.config.settings import get_agent_settings

router = APIRouter(tags=["健康"])


@router.get(
    "/health",
    response_model=ApiResponse[HealthResponse],
    summary="健康检查",
    description="Liveness 探测，进程存活即返回 ok。",
)
def health(request_id: str = Depends(get_request_id)) -> ApiResponse[HealthResponse]:
    root = resolve_project_root()
    agent_settings = get_agent_settings()
    backend_settings = get_backend_settings()
    payload = HealthResponse(
        status="ok",
        service="multi-agent-chat",
        model=agent_settings.openai_model,
        log_file=str(root / backend_settings.log_file),
        docs_url="/api/docs",
    )
    return ok(payload, request_id=request_id)


def _build_ready_checks(request: Request) -> ReadyResponse:
    backend_settings = get_backend_settings()
    agent_settings = get_agent_settings()
    checks: list[ReadyCheck] = []

    key_ok = bool(agent_settings.openai_api_key and agent_settings.openai_api_key.strip())
    checks.append(
        ReadyCheck(
            name="llm_api_key",
            ok=key_ok,
            detail=None if key_ok else "OPENAI_API_KEY 未配置",
        )
    )

    db_ok = False
    db_detail: str | None = None
    container = getattr(request.app.state, "container", None)
    database = getattr(container, "database", None) if container is not None else None
    if database is None:
        db_detail = "database container 未初始化"
    else:
        try:
            with database.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            db_ok = True
        except Exception as exc:
            db_detail = f"{type(exc).__name__}: {exc}"

    checks.append(
        ReadyCheck(
            name="chat_database",
            ok=db_ok,
            detail=db_detail,
        )
    )

    checkpoint_path = resolve_checkpoint_db_path()
    checkpoint_parent = checkpoint_path.parent
    checkpoint_ok = checkpoint_parent.exists() and checkpoint_parent.is_dir()
    checks.append(
        ReadyCheck(
            name="checkpoint_dir",
            ok=checkpoint_ok,
            detail=None if checkpoint_ok else f"目录不可写: {checkpoint_parent}",
        )
    )

    if backend_settings.is_production and not backend_settings.api_auth_key.strip():
        checks.append(
            ReadyCheck(
                name="api_auth_key",
                ok=False,
                detail="生产环境建议设置 API_AUTH_KEY",
            )
        )

    all_ok = all(item.ok for item in checks)
    return ReadyResponse(status="ready" if all_ok else "not_ready", checks=checks)


@router.get(
    "/ready",
    response_model=ApiResponse[ReadyResponse],
    summary="就绪检查",
    description="Readiness 探测，检查 LLM 密钥、会话库与 checkpoint 目录。",
)
def ready(
    request: Request,
    request_id: str = Depends(get_request_id),
) -> JSONResponse | ApiResponse[ReadyResponse]:
    payload = _build_ready_checks(request)
    body = ok(payload, request_id=request_id)
    status_code = 200 if payload.status == "ready" else 503
    if status_code == 200:
        return body
    return JSONResponse(status_code=status_code, content=body.model_dump())
