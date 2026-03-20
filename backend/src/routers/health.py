# backend/src/routers/health.py
"""GET /health エンドポイント定義."""
from fastapi import APIRouter, Depends

from src.config import Settings, get_settings
from src.models.response import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="ヘルスチェック")
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Cloud Run ヘルスチェック用エンドポイント.

    Returns:
        HealthResponse: status="ok" と実行環境。
    """
    return HealthResponse(environment=settings.environment)