"""Upload temporary model input images to GCS."""

from __future__ import annotations

import base64
import binascii
import uuid
from typing import Self

import structlog
from google.cloud.storage import Client as StorageClient

from src.config import Settings
from src.exceptions import NotConfiguredError

logger = structlog.get_logger(__name__)


class ModelInputImageUploader:
    """Store request images in GCS and return a gs:// URI."""

    def __init__(self: Self, settings: Settings) -> None:
        self._settings = settings

    def upload_base64_image(self: Self, image_base64: str) -> str:
        """Upload a base64 image to the configured input bucket."""
        if not self._settings.model_input_bucket_name:
            raise NotConfiguredError(
                message="モデル入力用 GCS bucket の設定が未完了です",
                detail="model_input_bucket_name is empty",
            )

        try:
            raw_bytes = base64.b64decode(image_base64, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise NotConfiguredError(
                message="画像データの形式が不正です",
                detail=str(exc),
            ) from exc

        blob_name = f"vertex-inputs/{uuid.uuid4()}.jpg"
        client = StorageClient(project=self._settings.gcp_project_id or None)
        bucket = client.bucket(self._settings.model_input_bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_string(raw_bytes, content_type="image/jpeg")

        gcs_uri = f"gs://{self._settings.model_input_bucket_name}/{blob_name}"
        logger.info(
            "model_input_image_uploaded",
            bucket_name=self._settings.model_input_bucket_name,
            blob_name=blob_name,
            byte_size=len(raw_bytes),
            gcs_uri=gcs_uri,
        )
        return gcs_uri
