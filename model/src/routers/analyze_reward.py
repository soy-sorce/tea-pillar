"""Reward analysis route."""

from __future__ import annotations

from collections.abc import Mapping

from fastapi import APIRouter, Body, HTTPException
from src.dependencies import get_reward_analyzer
from src.schemas import RewardAnalysisRequest

router = APIRouter(tags=["reward-analysis"])


def _to_optional_str(value: object) -> str | None:
    """Normalize optional string fields."""
    if value is None:
        return None
    return str(value)


def _to_request(payload: Mapping[str, object]) -> RewardAnalysisRequest:
    """Convert a JSON object into the domain request."""
    reaction_video_gcs_uri = payload.get("reaction_video_gcs_uri")
    if not isinstance(reaction_video_gcs_uri, str) or reaction_video_gcs_uri.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="reaction_video_gcs_uri must be a non-empty string",
        )

    return RewardAnalysisRequest(
        reaction_video_gcs_uri=reaction_video_gcs_uri,
        session_id=_to_optional_str(payload.get("session_id")),
        template_id=_to_optional_str(payload.get("template_id")),
        state_key=_to_optional_str(payload.get("state_key")),
    )


@router.post("/analyze-reward", response_model=None)
async def analyze_reward(body: object = Body(...)) -> dict[str, object]:
    """Analyze a reaction video and return reward metrics."""
    if not isinstance(body, Mapping):
        raise HTTPException(status_code=400, detail="request body must be a JSON object")
    request = _to_request(body)
    response = get_reward_analyzer().analyze(request=request)
    return response.to_dict()
