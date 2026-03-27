"""Health-related routes."""

from fastapi import APIRouter, Depends, Response

from src.config import Settings, get_settings
from src.models.response import HealthResponse, RootResponse
from src.services.rate_limit.dependencies import enforce_health_limit

router = APIRouter(tags=["health"])


@router.get("/", response_model=RootResponse, summary="Root endpoint")
async def root(
    settings: Settings = Depends(get_settings),
    _: None = Depends(enforce_health_limit),
) -> RootResponse:
    """Return a lightweight service descriptor for browsers and probes."""
    return RootResponse(service="nekkoflix-backend", environment=settings.environment)


@router.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    """Avoid noisy 404 logs from browsers requesting a favicon."""
    return Response(status_code=204)


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health(
    settings: Settings = Depends(get_settings),
    _: None = Depends(enforce_health_limit),
) -> HealthResponse:
    """Return runtime health information."""
    return HealthResponse(environment=settings.environment)
