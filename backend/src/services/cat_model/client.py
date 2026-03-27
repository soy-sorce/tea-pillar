"""Model service HTTP client."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Self, SupportsFloat, cast

import httpx
from src.config import Settings
from src.exceptions import ModelServiceError, ModelServiceTimeoutError, NotConfiguredError
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
        features = cast(Mapping[str, object], payload["features"])
        aux_labels = cast(Mapping[str, object], payload["aux_labels"])
        return CatFeatures(
            features={str(key): _as_float(value) for key, value in features.items()},
            emotion_label=str(aux_labels["emotion_label"]),
            clip_top_label=str(aux_labels["clip_top_label"]),
            meow_label=(
                str(aux_labels["meow_label"]) if aux_labels.get("meow_label") is not None else None
            ),
            predicted_rewards={
                str(key): _as_float(value)
                for key, value in cast(
                    Mapping[str, object],
                    payload.get("predicted_rewards", {}),
                ).items()
            },
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
        return RewardAnalysisResult(
            paw_hit_count=int(payload["paw_hit_count"]),
            gaze_duration_seconds=_as_float(payload["gaze_duration_seconds"]),
            reward=_as_float(payload["reward"]),
            analysis_model_versions={
                str(key): str(value)
                for key, value in cast(
                    Mapping[str, object],
                    payload["analysis_model_versions"],
                ).items()
            },
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
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(f"{base_url}{path}", json=body)
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


def _as_float(value: object) -> float:
    return float(cast(SupportsFloat, value))
