# backend/src/app.py
"""FastAPI アプリケーション定義.

ミドルウェア・ルーター・例外ハンドラーをここで組み立てる。
"""
import time
import uuid
from collections.abc import Callable
from typing import Any

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings
from src.exceptions import NekkoflixBaseError
from src.logging_config import configure_logging
from src.routers import feedback, generate, health

logger = structlog.get_logger(__name__)
settings = get_settings()


def create_app() -> FastAPI:
    """FastAPI アプリケーションを生成して返す.

    Returns:
        FastAPI: 設定済みのアプリケーションインスタンス。
    """
    app = FastAPI(
        title="nekkoflix API",
        description="猫のための動画生成API",
        version="1.0.0",
    )

    # ── ミドルウェア ──────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # API GatewayでJWT検証するためBackend側は制限しない
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_request_id(request: Request, call_next: Any) -> Response:
        """リクエストIDをヘッダーに付与し、ログに含める."""
        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        with structlog.contextvars.bind_contextvars(request_id=request_id):
            logger.info(
                "request_start",
                method=request.method,
                path=request.url.path,
            )
            response = await call_next(request)
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            logger.info(
                "request_end",
                status_code=response.status_code,
                duration_ms=duration_ms,
            )

        response.headers["X-Request-ID"] = request_id
        return response

    # ── ルーター登録 ──────────────────────────────────────────────
    app.include_router(health.router)
    app.include_router(generate.router)
    app.include_router(feedback.router)

    # ── 例外ハンドラー ────────────────────────────────────────────
    @app.exception_handler(NekkoflixBaseError)
    async def nekkoflix_error_handler(
        request: Request,
        exc: NekkoflixBaseError,
    ) -> Response:
        """アプリケーション独自例外のハンドラー."""
        logger.error(
            "application_error",
            error_code=exc.error_code,
            message=exc.message,
        )
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": exc.error_code,
                "message": exc.message,
            },
        )

    return app


app = create_app()