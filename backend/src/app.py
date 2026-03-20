"""FastAPI application entrypoint."""

import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from src.config import get_settings
from src.exceptions import InvalidInputError, NekkoflixBaseError
from src.logging_config import configure_logging
from src.routers import feedback, generate, health

logger = structlog.get_logger(__name__)

FRONTEND_ORIGIN = "https://video-gen4cat-frontend-94553428765.asia-northeast1.run.app"
FORCED_LOG_LEVEL = "DEBUG"


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    configure_logging(log_level=FORCED_LOG_LEVEL)
    logger.info(
        "app_startup_config",
        environment=settings.environment,
        log_level=FORCED_LOG_LEVEL,
        gcp_project_id=settings.gcp_project_id,
        gcp_region=settings.gcp_region,
        vertex_endpoint_location=settings.vertex_endpoint_location,
    )
    logger.debug(
        "app_startup_config_detail",
        vertex_endpoint_id=settings.vertex_endpoint_id,
        gcs_bucket_name=settings.gcs_bucket_name,
        firestore_database_id=settings.firestore_database_id,
        gemini_model=settings.gemini_model,
        veo_model=settings.veo_model,
    )

    app = FastAPI(
        title="nekkoflix API",
        description="Cats-first video generation backend",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[FRONTEND_ORIGIN],
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
        allow_credentials=False,
    )

    @app.middleware("http")
    async def add_request_id(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = str(uuid.uuid4())
        start = time.perf_counter()

        with structlog.contextvars.bound_contextvars(request_id=request_id):
            logger.info("request_start", method=request.method, path=request.url.path)
            response = await call_next(request)
            duration_ms = int((time.perf_counter() - start) * 1000)
            logger.info(
                "request_end",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
            )

        response.headers["X-Request-ID"] = request_id
        return response

    @app.exception_handler(NekkoflixBaseError)
    async def handle_nekkoflix_error(
        request: Request,
        exc: NekkoflixBaseError,
    ) -> JSONResponse:
        logger.error(
            "application_error",
            path=request.url.path,
            error_code=exc.error_code,
            message=exc.message,
            detail=exc.detail,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_response_content(),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        error = InvalidInputError(
            message="入力データに問題があります",
            detail=str(exc),
        )
        logger.warning(
            "request_validation_error",
            path=request.url.path,
            detail=str(exc),
        )
        return JSONResponse(
            status_code=error.status_code,
            content=error.to_response_content(),
        )

    app.include_router(health.router)
    app.include_router(generate.router)
    app.include_router(feedback.router)
    return app


app = create_app()
