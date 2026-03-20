"""POST /generate route."""

from fastapi import APIRouter, Depends

from src.config import Settings, get_settings
from src.models.request import GenerateRequest
from src.models.response import ErrorResponse, GenerateResponse
from src.services.orchestrator import GenerateOrchestrator

router = APIRouter(tags=["generate"])


@router.post(
    "/generate",
    response_model=GenerateResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
        504: {"model": ErrorResponse},
    },
    summary="Generate a cat-tailored video",
)
async def generate(
    request: GenerateRequest,
    settings: Settings = Depends(get_settings),
) -> GenerateResponse:
    """Execute the end-to-end generation flow."""
    orchestrator = GenerateOrchestrator(settings=settings)
    return await orchestrator.execute(request=request)
