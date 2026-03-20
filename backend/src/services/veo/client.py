"""Veo video generation client."""

import asyncio
import json
import time
from typing import Any, cast

import structlog
import vertexai
from google.api_core.exceptions import DeadlineExceeded, GoogleAPICallError, RetryError
from google.cloud import aiplatform_v1

from src.config import Settings
from src.exceptions import NotConfiguredError, VeoGenerationError, VeoTimeoutError

logger = structlog.get_logger(__name__)


class VeoClient:
    """Submit Veo generation and poll until it finishes."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def generate(self, prompt: str) -> str:
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
        client = aiplatform_v1.PredictionServiceAsyncClient()
        endpoint = (
            f"projects/{self._settings.gcp_project_id}"
            f"/locations/{self._settings.gcp_region}"
            f"/publishers/google/models/{self._settings.veo_model}"
        )

        try:
            operation = await client.predict(
                endpoint=endpoint,
                instances=[{"prompt": prompt}],
                parameters={
                    "generate_audio": False,
                    "output_gcs_uri": f"gs://{self._settings.gcs_bucket_name}/",
                },
            )
        except DeadlineExceeded as exc:
            raise VeoTimeoutError(detail=str(exc)) from exc
        except RetryError as exc:
            raise VeoTimeoutError(detail=str(exc)) from exc
        except GoogleAPICallError as exc:
            raise VeoGenerationError(detail=str(exc)) from exc

        logger.info(
            "veo_generation_started",
            model=self._settings.veo_model,
            prompt_length=len(prompt),
            operation_name=operation.operation.name,
        )
        return await self._poll_until_done(operation_name=operation.operation.name)

    async def _poll_until_done(self, operation_name: str) -> str:
        """Poll the long-running operation."""
        operations_module = cast(Any, aiplatform_v1)
        operations_client = operations_module.OperationsAsyncClient()
        started_at = time.monotonic()

        while True:
            elapsed = time.monotonic() - started_at
            if elapsed > self._settings.veo_timeout:
                raise VeoTimeoutError(
                    detail=f"timed out after {self._settings.veo_timeout}s",
                )

            operation = await operations_client.get_operation(name=operation_name)
            if operation.done:
                if operation.error.code != 0:
                    raise VeoGenerationError(detail=operation.error.message)
                gcs_uri = self._extract_gcs_uri(operation.response.value)
                logger.info(
                    "veo_generation_completed",
                    operation_name=operation_name,
                    elapsed_seconds=int(elapsed),
                    gcs_uri=gcs_uri,
                )
                return gcs_uri

            logger.debug(
                "veo_polling",
                operation_name=operation_name,
                elapsed_seconds=int(elapsed),
            )
            await asyncio.sleep(self._settings.veo_polling_interval)

    def _extract_gcs_uri(self, raw_response: bytes) -> str:
        """Extract the output URI from a conservative set of response formats."""
        decoded = raw_response.decode() if isinstance(raw_response, bytes) else str(raw_response)
        try:
            payload = cast(dict[str, object], json.loads(decoded))
        except json.JSONDecodeError as exc:
            if decoded.startswith("gs://"):
                return decoded
            raise VeoGenerationError(
                message="Veo の出力形式を解釈できませんでした",
                detail=decoded,
            ) from exc

        candidate_keys = ("gcs_uri", "output_gcs_uri", "uri")
        for key in candidate_keys:
            value = payload.get(key)
            if isinstance(value, str) and value.startswith("gs://"):
                return value

        artifacts = payload.get("artifacts")
        if isinstance(artifacts, list):
            for artifact in artifacts:
                if isinstance(artifact, dict):
                    uri = artifact.get("gcs_uri") or artifact.get("uri")
                    if isinstance(uri, str) and uri.startswith("gs://"):
                        return uri

        raise VeoGenerationError(
            message="Veo の出力形式を解釈できませんでした",
            detail=decoded,
        )
