"""GET /health route."""

from fastapi import APIRouter, Depends

from src.config import Settings, get_settings
from src.models.response import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Return runtime health information."""
    return HealthResponse(environment=settings.environment)
