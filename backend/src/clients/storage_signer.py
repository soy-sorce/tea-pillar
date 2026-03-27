"""GCS signed URL generator."""

from datetime import timedelta
from pathlib import Path
from typing import Self, cast
from urllib.parse import urlparse

import google.auth
import structlog
from google.auth.transport.requests import Request
from google.cloud.storage import Client as StorageClient
from google.oauth2 import service_account

from src.config import Settings
from src.exceptions import NotConfiguredError, VeoGenerationError

logger = structlog.get_logger(__name__)


class SignedUrlGenerator:
    """Generate signed URLs for generated videos."""

    def __init__(self: Self, settings: Settings) -> None:
        self._settings = settings

    def generate(self: Self, gcs_uri: str) -> str:
        """Convert a gs:// URI to a temporary signed URL."""
        if not self._settings.gcp_project_id:
            raise NotConfiguredError(
                message="GCS Signed URL の設定が未完了です",
                detail="gcp_project_id is empty",
            )

        bucket_name, blob_name = self._parse_gcs_uri(gcs_uri)
        client = self._build_storage_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        signed_url_kwargs: dict[str, object] = {
            "version": "v4",
            "method": "GET",
            "expiration": timedelta(
                hours=self._settings.gcs_signed_url_expiration_hours,
            ),
        }

        if not self._is_local_signing_mode():
            service_account_email, access_token = self._resolve_runtime_signing_identity()
            signed_url_kwargs["service_account_email"] = service_account_email
            signed_url_kwargs["access_token"] = access_token

        signed_url = blob.generate_signed_url(**signed_url_kwargs)
        logger.info("signed_url_generated", bucket_name=bucket_name, blob_name=blob_name)
        return cast(str, signed_url)

    def _build_storage_client(self: Self) -> StorageClient:
        """Use a local service account key for signing during development."""
        local_credentials_path = self._get_local_signing_credentials_path()
        if local_credentials_path is not None:
            logger.info(
                "signed_url_using_local_service_account",
                credentials_path=str(local_credentials_path),
            )
            credentials = service_account.Credentials.from_service_account_file(
                str(local_credentials_path)
            )  # type: ignore[no-untyped-call]
            return StorageClient(
                project=self._settings.gcp_project_id,
                credentials=credentials,
            )

        return StorageClient(project=self._settings.gcp_project_id)

    def _is_local_signing_mode(self: Self) -> bool:
        return self._get_local_signing_credentials_path() is not None

    def _get_local_signing_credentials_path(self: Self) -> Path | None:
        configured_path = self._settings.gcs_signing_service_account_file.strip()
        if self._settings.environment != "development" or not configured_path:
            return None

        credentials_path = Path(configured_path)
        if not credentials_path.exists():
            logger.warning(
                "signed_url_local_service_account_missing",
                credentials_path=str(credentials_path),
            )
            return None

        return credentials_path

    def _resolve_runtime_signing_identity(self: Self) -> tuple[str, str]:
        credentials, _ = google.auth.default()
        request = Request()
        credentials.refresh(request)  # type: ignore[no-untyped-call]

        service_account_email = cast(
            str | None,
            getattr(credentials, "service_account_email", None),
        )
        token = cast(str | None, getattr(credentials, "token", None))

        if not service_account_email:
            raise NotConfiguredError(
                message="GCS Signed URL の設定が未完了です",
                detail="runtime credentials do not expose service_account_email",
            )
        if not token:
            raise NotConfiguredError(
                message="GCS Signed URL の設定が未完了です",
                detail="runtime credentials did not return an access token",
            )

        return service_account_email, token

    def _parse_gcs_uri(self: Self, gcs_uri: str) -> tuple[str, str]:
        parsed = urlparse(gcs_uri)
        blob_name = parsed.path.lstrip("/")
        if parsed.scheme != "gs" or not parsed.netloc or not blob_name:
            raise VeoGenerationError(
                message="Veo の出力 URI が不正です",
                detail=f"gcs_uri={gcs_uri}",
            )
        return parsed.netloc, blob_name
