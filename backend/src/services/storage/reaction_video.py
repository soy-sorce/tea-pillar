"""Reaction video storage helpers."""

from __future__ import annotations

from datetime import timedelta
from typing import Self
from urllib.parse import urlparse
from uuid import uuid4

from google.cloud.storage import Client as StorageClient
from src.config import Settings
from src.exceptions import NotConfiguredError, ReactionVideoUploadError


class ReactionVideoStorageService:
    """Issue signed upload URLs and validate uploaded object URIs."""

    _OBJECT_PREFIX = "reaction_videos"

    def __init__(self: Self, settings: Settings) -> None:
        self._settings = settings

    def issue_upload_url(self: Self, *, session_id: str) -> tuple[str, str]:
        bucket_name = self._settings.reaction_video_bucket_name
        if not bucket_name or not self._settings.gcp_project_id:
            raise NotConfiguredError(
                message="反応動画バケットの設定が未完了です",
                detail="reaction_video_bucket_name or gcp_project_id is empty",
            )

        object_name = f"{self._OBJECT_PREFIX}/{session_id}/{uuid4()}.mp4"
        try:
            client = StorageClient(project=self._settings.gcp_project_id)
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(object_name)
            upload_url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(
                    seconds=self._settings.reaction_video_upload_url_expires_seconds
                ),
                method="PUT",
                content_type="video/mp4",
            )
        except Exception as exc:  # pragma: no cover - external API mapping
            raise ReactionVideoUploadError(
                message="反応動画 upload URL の発行に失敗しました",
                detail=str(exc),
            ) from exc

        return upload_url, f"gs://{bucket_name}/{object_name}"

    def validate_gcs_uri(self: Self, *, session_id: str, reaction_video_gcs_uri: str) -> str:
        bucket_name = self._settings.reaction_video_bucket_name
        expected_prefix = f"{self._OBJECT_PREFIX}/{session_id}/"
        parsed = urlparse(reaction_video_gcs_uri)

        if parsed.scheme != "gs" or not parsed.netloc or not parsed.path:
            raise ReactionVideoUploadError(
                message="反応動画 URI の形式が不正です",
                detail=f"uri={reaction_video_gcs_uri}",
            )
        if parsed.netloc != bucket_name:
            raise ReactionVideoUploadError(
                message="反応動画 URI のバケットが不正です",
                detail=f"uri={reaction_video_gcs_uri}",
            )
        object_name = parsed.path.lstrip("/")
        if not object_name.startswith(expected_prefix):
            raise ReactionVideoUploadError(
                message="反応動画 URI の保存先が不正です",
                detail=f"uri={reaction_video_gcs_uri}",
            )
        return reaction_video_gcs_uri
