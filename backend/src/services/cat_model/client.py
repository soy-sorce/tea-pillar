"""Vertex AI custom endpoint client."""

import asyncio
from collections.abc import Mapping
from typing import cast

import structlog
from google.api_core.exceptions import DeadlineExceeded, GoogleAPICallError, RetryError
from google.cloud import aiplatform

from src.config import Settings
from src.exceptions import NotConfiguredError, VertexAIError, VertexAITimeoutError
from src.models.internal import CatFeatures
from src.services.cat_model.schemas import EndpointPrediction

logger = structlog.get_logger(__name__)


class CatModelClient:
    """Client for the v1 custom endpoint."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def predict(
        self,
        image_base64: str,
        audio_base64: str | None,
        candidate_video_ids: list[str],
    ) -> CatFeatures:
        """Call the custom endpoint and normalize its response."""
        if not self._settings.gcp_project_id or not self._settings.vertex_endpoint_id:
            raise NotConfiguredError(
                message="Vertex AI Endpoint の設定が未完了です",
                detail="gcp_project_id or vertex_endpoint_id is empty",
            )

        endpoint = aiplatform.Endpoint(
            endpoint_name=self._settings.vertex_endpoint_id,
            project=self._settings.gcp_project_id,
            location=self._settings.vertex_endpoint_location,
        )

        instance: dict[str, str | list[str] | None] = {
            "image_base64": image_base64,
            "audio_base64": audio_base64,
            "candidate_video_ids": candidate_video_ids,
        }
        logger.info(
            "cat_model_predict_start",
            endpoint_id=self._settings.vertex_endpoint_id,
            has_audio=audio_base64 is not None,
            candidate_count=len(candidate_video_ids),
        )

        try:
            response = await asyncio.to_thread(
                endpoint.predict,
                instances=[instance],
                timeout=self._settings.vertex_prediction_timeout,
            )
        except DeadlineExceeded as exc:
            raise VertexAITimeoutError(detail=str(exc)) from exc
        except RetryError as exc:
            raise VertexAITimeoutError(detail=str(exc)) from exc
        except GoogleAPICallError as exc:
            raise VertexAIError(detail=str(exc)) from exc

        prediction = response.predictions[0]
        parsed = self._parse_prediction(prediction=prediction)
        logger.info(
            "cat_model_predict_done",
            emotion_label=parsed.emotion_label,
            clip_top_label=parsed.clip_top_label,
            meow_label=parsed.meow_label or "unknown",
            predicted_reward_count=len(parsed.predicted_rewards),
        )
        return parsed

    def _parse_prediction(
        self,
        prediction: EndpointPrediction | dict[str, object],
    ) -> CatFeatures:
        """Normalize endpoint output to CatFeatures."""
        features = cast(Mapping[str, object], prediction["features"])
        aux_labels = cast(Mapping[str, object], prediction["aux_labels"])
        raw_predicted_rewards = cast(
            Mapping[str, object],
            prediction["predicted_rewards"],
        )
        predicted_rewards = {
            str(video_id): float(cast(float, score))
            for video_id, score in raw_predicted_rewards.items()
        }
        return CatFeatures(
            features={str(name): float(cast(float, value)) for name, value in features.items()},
            emotion_label=str(aux_labels["emotion_label"]),
            clip_top_label=str(aux_labels["clip_top_label"]),
            meow_label=(
                str(aux_labels["meow_label"]) if aux_labels.get("meow_label") is not None else None
            ),
            predicted_rewards=predicted_rewards,
        )
