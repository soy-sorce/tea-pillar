"""GCS signed URL generator."""

from datetime import timedelta
from pathlib import Path
from typing import Self, cast

import google.auth
import structlog
from google.auth.transport.requests import Request
from google.cloud.storage import Client as StorageClient
from google.oauth2 import service_account
from src.config import Settings
from src.exceptions import NotConfiguredError

logger = structlog.get_logger(__name__)

_LOCAL_SIGNING_CREDENTIALS_PATH = Path(
    "/home/shouh/team_project/GCP_hackathon_2026/.gcp_secret_key/gcp-hackathon-2026-031ad44f0516.json"
)


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

        without_scheme = gcs_uri.removeprefix("gs://")
        bucket_name, blob_name = without_scheme.split("/", 1)
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

        # On Cloud Run, ADC usually resolves to token-only credentials. For signed URLs,
        # pass an access token plus the signer service account email so the library can
        # use IAMCredentials SignBlob instead of requiring a local private key file.
        if not self._is_local_signing_mode():
            service_account_email, access_token = self._resolve_runtime_signing_identity()
            signed_url_kwargs["service_account_email"] = service_account_email
            signed_url_kwargs["access_token"] = access_token

        signed_url = blob.generate_signed_url(**signed_url_kwargs)
        logger.info("signed_url_generated", bucket_name=bucket_name, blob_name=blob_name)
        return cast(str, signed_url)

    def _build_storage_client(self: Self) -> StorageClient:
        """Use a local service account key for signing during development."""
        if self._is_local_signing_mode():
            logger.info(
                "signed_url_using_local_service_account",
                credentials_path=str(_LOCAL_SIGNING_CREDENTIALS_PATH),
            )
            credentials = service_account.Credentials.from_service_account_file(
                str(_LOCAL_SIGNING_CREDENTIALS_PATH)
            )  # type: ignore[no-untyped-call]
            return StorageClient(
                project=self._settings.gcp_project_id,
                credentials=credentials,
            )

        return StorageClient(project=self._settings.gcp_project_id)

    def _is_local_signing_mode(self: Self) -> bool:
        return (
            self._settings.environment == "development" and _LOCAL_SIGNING_CREDENTIALS_PATH.exists()
        )

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
