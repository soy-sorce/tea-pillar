"""Prediction route with Vertex-compatible envelope support."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from fastapi import APIRouter, Body, HTTPException
from src.dependencies import get_predictor
from src.schemas import PredictionRequest

router = APIRouter(tags=["predict"])


def _to_optional_str(value: object) -> str | None:
    """Normalize optional string fields."""
    if value is None:
        return None
    return str(value)


def _to_request(payload: Mapping[str, object]) -> PredictionRequest:
    """Convert a JSON object into the domain request."""
    candidate_video_ids_raw = payload.get("candidate_video_ids")
    if not isinstance(candidate_video_ids_raw, Sequence) or isinstance(
        candidate_video_ids_raw,
        str,
    ):
        raise HTTPException(
            status_code=400,
            detail="candidate_video_ids must be an array of strings",
        )

    return PredictionRequest(
        image_base64=_to_optional_str(payload.get("image_base64")),
        image_gcs_uri=_to_optional_str(payload.get("image_gcs_uri")),
        audio_base64=_to_optional_str(payload.get("audio_base64")),
        candidate_video_ids=[str(item) for item in candidate_video_ids_raw],
    )


def _parse_request_body(body: object) -> tuple[PredictionRequest, bool]:
    """Accept either the Vertex envelope or a plain local request body."""
    if not isinstance(body, Mapping):
        raise HTTPException(status_code=400, detail="request body must be a JSON object")

    instances = body.get("instances")
    if instances is None:
        return _to_request(body), False

    if not isinstance(instances, Sequence) or isinstance(instances, str):
        raise HTTPException(status_code=400, detail="instances must be an array")
    if len(instances) == 0:
        raise HTTPException(status_code=400, detail="instances must not be empty")

    first_instance = instances[0]
    if not isinstance(first_instance, Mapping):
        raise HTTPException(status_code=400, detail="instances[0] must be a JSON object")

    return _to_request(first_instance), True


@router.post("/predict", response_model=None)
async def predict(body: object = Body(...)) -> dict[str, object]:
    """Run model prediction and return the local or Vertex-compatible response."""
    request, is_vertex_envelope = _parse_request_body(body)
    response = get_predictor().predict(request=request).to_dict()
    if is_vertex_envelope:
        return {"predictions": [response]}
    return response
