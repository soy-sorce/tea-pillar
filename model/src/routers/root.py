"""Root route for service metadata."""

from fastapi import APIRouter

from ..artifacts import get_artifact_source

router = APIRouter(tags=["root"])


@router.get("/")
async def root() -> dict[str, str]:
    """Return a small service descriptor."""
    return {
        "service": "nekkoflix-model",
        "status": "ok",
        "artifact_source": get_artifact_source(),
        "predict_endpoint": "/predict",
        "reward_analysis_endpoint": "/analyze-reward",
    }
