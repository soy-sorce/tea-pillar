"""Model service HTTP client."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Self, cast

import httpx
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from pydantic import ValidationError

from src.config import Settings
from src.exceptions import ModelServiceError, ModelServiceTimeoutError, NotConfiguredError
from src.models.external import ModelPredictResponse, ModelRewardAnalysisResponse
from src.models.internal import CatFeatures, RewardAnalysisResult


class CatModelClient:
    """Client for the Cloud Run model service."""

    def __init__(self: Self, settings: Settings) -> None:
        self._settings = settings

    async def predict(
        self: Self,
        image_base64: str,
        audio_base64: str | None,
        candidate_video_ids: list[str],
    ) -> CatFeatures:
        """Call `/predict` and normalize the response."""
        body = {
            "image_base64": image_base64,
            "audio_base64": audio_base64,
            "candidate_video_ids": candidate_video_ids,
        }
        payload = await self._post_json(path="/predict", body=body)
        try:
            response = ModelPredictResponse.model_validate(payload)
        except ValidationError as exc:
            raise ModelServiceError(detail=f"invalid /predict response: {exc}") from exc

        return CatFeatures(
            features=response.features,
            emotion_label=response.aux_labels.emotion_label,
            clip_top_label=response.aux_labels.clip_top_label,
            meow_label=response.aux_labels.meow_label,
            predicted_rewards=response.predicted_rewards,
        )

    async def analyze_reward(
        self: Self,
        reaction_video_gcs_uri: str,
        *,
        session_id: str,
        template_id: str,
        state_key: str,
    ) -> RewardAnalysisResult:
        """Call `/analyze-reward` and normalize the response."""
        body = {
            "reaction_video_gcs_uri": reaction_video_gcs_uri,
            "session_id": session_id,
            "template_id": template_id,
            "state_key": state_key,
        }
        payload = await self._post_json(path="/analyze-reward", body=body)
        try:
            response = ModelRewardAnalysisResponse.model_validate(payload)
        except ValidationError as exc:
            raise ModelServiceError(detail=f"invalid /analyze-reward response: {exc}") from exc

        return RewardAnalysisResult(
            paw_hit_count=response.paw_hit_count,
            gaze_duration_seconds=response.gaze_duration_seconds,
            reward=response.reward,
            analysis_model_versions=response.analysis_model_versions,
        )

    async def _post_json(
        self: Self,
        *,
        path: str,
        body: Mapping[str, object],
    ) -> Mapping[str, Any]:
        base_url = self._settings.model_service_url.rstrip("/")
        if not base_url:
            raise NotConfiguredError(
                message="モデルサービスの設定が未完了です",
                detail="model_service_url is empty",
            )

        timeout = httpx.Timeout(self._settings.model_service_timeout_seconds)
        headers = {"Authorization": f"Bearer {self._get_identity_token(base_url)}"}
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(f"{base_url}{path}", json=body, headers=headers)
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise ModelServiceTimeoutError(detail=str(exc)) from exc
        except httpx.HTTPStatusError as exc:
            raise ModelServiceError(detail=f"status={exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            raise ModelServiceError(detail=str(exc)) from exc

        data = response.json()
        if not isinstance(data, Mapping):
            raise ModelServiceError(detail="response body must be a JSON object")
        return cast(Mapping[str, Any], data)

    def _get_identity_token(self: Self, audience: str) -> str:
        try:
            token = cast(
                str | None,
                id_token.fetch_id_token(Request(), audience),  # type: ignore[no-untyped-call]
            )
        except Exception as exc:
            raise ModelServiceError(detail=f"id_token_fetch_failed: {exc}") from exc

        if not token:
            raise ModelServiceError(detail="id_token_fetch_failed: empty token")
        return token
