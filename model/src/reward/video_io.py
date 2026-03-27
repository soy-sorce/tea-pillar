"""Video loading helpers for reward analysis."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from google.cloud.storage import Client as StorageClient


@dataclass(slots=True)
class VideoClip:
    """Local reward-analysis input clip."""

    source_uri: str
    local_path: Path

    @classmethod
    def from_gcs_uri(cls: type[Self], gcs_uri: str) -> Self:
        """Download a GCS object to a local temporary file."""
        bucket_name, object_name = _split_gcs_uri(gcs_uri)
        temp_file = tempfile.NamedTemporaryFile(
            suffix=Path(object_name).suffix or ".mp4",
            delete=False,
        )
        temp_path = Path(temp_file.name)
        temp_file.close()

        client = StorageClient()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(object_name)
        blob.download_to_filename(str(temp_path))
        return cls(source_uri=gcs_uri, local_path=temp_path)


def _split_gcs_uri(gcs_uri: str) -> tuple[str, str]:
    """Split a `gs://bucket/object` URI."""
    if not gcs_uri.startswith("gs://"):
        raise ValueError(f"unsupported GCS URI: {gcs_uri}")
    trimmed = gcs_uri[5:]
    bucket_name, _, object_name = trimmed.partition("/")
    if not bucket_name or not object_name:
        raise ValueError(f"invalid GCS URI: {gcs_uri}")
    return bucket_name, object_name
