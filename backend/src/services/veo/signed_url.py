"""GCS signed URL generator."""

from datetime import timedelta
from typing import cast

import structlog
from google.cloud.storage import Client as StorageClient

from src.config import Settings
from src.exceptions import NotConfiguredError

logger = structlog.get_logger(__name__)


class SignedUrlGenerator:
    """Generate signed URLs for generated videos."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def generate(self, gcs_uri: str) -> str:
        """Convert a gs:// URI to a temporary signed URL."""
        if not self._settings.gcp_project_id:
            raise NotConfiguredError(
                message="GCS Signed URL の設定が未完了です",
                detail="gcp_project_id is empty",
            )

        without_scheme = gcs_uri.removeprefix("gs://")
        bucket_name, blob_name = without_scheme.split("/", 1)
        client = StorageClient(project=self._settings.gcp_project_id)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        signed_url = blob.generate_signed_url(
            version="v4",
            method="GET",
            expiration=timedelta(
                hours=self._settings.gcs_signed_url_expiration_hours,
            ),
        )
        logger.info("signed_url_generated", bucket_name=bucket_name, blob_name=blob_name)
        return cast(str, signed_url)
