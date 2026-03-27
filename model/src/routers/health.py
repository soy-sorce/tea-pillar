"""Health route."""

from fastapi import APIRouter
from src.artifacts import get_artifact_source
from src.dependencies import _predictor

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "ok",
        "predictor_loaded": "true" if _predictor is not None else "false",
        "reward_analyzer_loaded": "true",
        "artifact_source": get_artifact_source(),
    }
