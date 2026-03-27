"""Veo video generation client."""

import asyncio
import time
from typing import Self

import structlog
import vertexai
from google.api_core.exceptions import DeadlineExceeded, GoogleAPICallError, RetryError
from google.genai import Client, types

from src.config import Settings
from src.exceptions import NotConfiguredError, VeoGenerationError, VeoTimeoutError

logger = structlog.get_logger(__name__)


class VeoClient:
    """Submit Veo generation and poll until it finishes."""

    def __init__(self: Self, settings: Settings) -> None:
        self._settings = settings

    async def generate(self: Self, prompt: str) -> str:
        """Generate a video and return its GCS URI."""
        if not self._settings.gcp_project_id or not self._settings.gcs_bucket_name:
            raise NotConfiguredError(
                message="Veo / GCS の設定が未完了です",
                detail="gcp_project_id or gcs_bucket_name is empty",
            )

        vertexai.init(
            project=self._settings.gcp_project_id,
            location=self._settings.gcp_region,
        )
        client = Client(
            vertexai=True,
            project=self._settings.gcp_project_id,
            location="global",
        )
        logger.info(
            "veo_generation_request_start",
            model=self._settings.veo_model,
            project_id=self._settings.gcp_project_id,
            location=self._settings.gcp_region,
            bucket_name=self._settings.gcs_bucket_name,
            prompt_length=len(prompt),
        )
        logger.debug(
            "veo_generation_request_detail",
            veo_sdk_location="global",
            output_gcs_uri=f"gs://{self._settings.gcs_bucket_name}/",
            prompt_preview=prompt[:500],
        )

        try:
            operation = await asyncio.to_thread(
                client.models.generate_videos,
                model=self._settings.veo_model,
                prompt=prompt,
                config=types.GenerateVideosConfig(
                    generate_audio=self._settings.veo_generate_audio,
                    output_gcs_uri=f"gs://{self._settings.gcs_bucket_name}/",
                    duration_seconds=self._settings.veo_duration_seconds,
                ),
            )
        except DeadlineExceeded as exc:
            logger.exception(
                "veo_predict_deadline_exceeded",
                model=self._settings.veo_model,
            )
            raise VeoTimeoutError(detail=str(exc)) from exc
        except RetryError as exc:
            logger.exception(
                "veo_predict_retry_timeout",
                model=self._settings.veo_model,
            )
            raise VeoTimeoutError(detail=str(exc)) from exc
        except GoogleAPICallError as exc:
            logger.exception(
                "veo_predict_google_api_error",
                model=self._settings.veo_model,
                error_type=type(exc).__name__,
            )
            raise VeoGenerationError(detail=str(exc)) from exc

        logger.info(
            "veo_generation_started",
            model=self._settings.veo_model,
            prompt_length=len(prompt),
            operation_name=operation.name,
        )
        return await self._poll_until_done(client=client, operation=operation)

    async def _poll_until_done(
        self: Self,
        client: Client,
        operation: types.GenerateVideosOperation,
    ) -> str:
        """Poll the long-running operation."""
        started_at = time.monotonic()

        while True:
            elapsed = time.monotonic() - started_at
            if elapsed > self._settings.veo_timeout:
                raise VeoTimeoutError(
                    detail=f"timed out after {self._settings.veo_timeout}s",
                )

            operation = await asyncio.to_thread(client.operations.get, operation)
            if operation.done:
                if getattr(operation, "error", None):
                    logger.error(
                        "veo_generation_operation_failed",
                        operation_name=operation.name,
                        error_code=getattr(operation.error, "code", "unknown"),
                        error_message=getattr(operation.error, "message", "unknown"),
                    )
                    raise VeoGenerationError(
                        detail=getattr(operation.error, "message", "unknown"),
                    )
                gcs_uri = self._extract_gcs_uri(operation)
                logger.info(
                    "veo_generation_completed",
                    operation_name=operation.name,
                    elapsed_seconds=int(elapsed),
                    gcs_uri=gcs_uri,
                )
                return gcs_uri

            logger.debug(
                "veo_polling",
                operation_name=operation.name,
                elapsed_seconds=int(elapsed),
            )
            await asyncio.sleep(self._settings.veo_polling_interval)

    def _extract_gcs_uri(self: Self, operation: types.GenerateVideosOperation) -> str:
        """Extract the output URI from the completed SDK operation."""
        response = operation.result or operation.response
        generated_videos = response.generated_videos if response is not None else None
        if generated_videos:
            for generated_video in generated_videos:
                video = generated_video.video
                if video is not None and video.uri and video.uri.startswith("gs://"):
                    return video.uri

        raise VeoGenerationError(
            message="Veo の出力形式を解釈できませんでした",
            detail=str(operation),
        )
