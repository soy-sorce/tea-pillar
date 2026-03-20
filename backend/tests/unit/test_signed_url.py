"""Unit tests for signed URL generation."""

from __future__ import annotations

from pytest import MonkeyPatch
from src.config import Settings
from src.exceptions import NotConfiguredError
from src.services.veo.signed_url import SignedUrlGenerator


def test_generate_raises_when_project_is_missing() -> None:
    generator = SignedUrlGenerator(settings=Settings(gcp_project_id=""))

    try:
        generator.generate("gs://bucket/path/video.mp4")
    except NotConfiguredError as exc:
        assert exc.error_code == "NOT_CONFIGURED"
    else:
        raise AssertionError("NotConfiguredError was not raised")


def test_generate_builds_signed_url(monkeypatch: MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakeBlob:
        def __init__(self, name: str) -> None:
            self.name = name

        def generate_signed_url(self, **kwargs: object) -> str:
            captured.update(kwargs)
            return "https://signed.example/video.mp4"

    class FakeBucket:
        def __init__(self, name: str) -> None:
            self.name = name

        def blob(self, blob_name: str) -> FakeBlob:
            captured["bucket_name"] = self.name
            captured["blob_name"] = blob_name
            return FakeBlob(blob_name)

    class FakeStorageClient:
        def __init__(self, project: str) -> None:
            captured["project"] = project

        def bucket(self, bucket_name: str) -> FakeBucket:
            return FakeBucket(bucket_name)

    monkeypatch.setattr(
        "src.services.veo.signed_url.StorageClient",
        FakeStorageClient,
    )
    generator = SignedUrlGenerator(
        settings=Settings(gcp_project_id="demo-project", gcs_signed_url_expiration_hours=3),
    )

    url = generator.generate("gs://bucket/path/to/video.mp4")

    assert url == "https://signed.example/video.mp4"
    assert captured["project"] == "demo-project"
    assert captured["bucket_name"] == "bucket"
    assert captured["blob_name"] == "path/to/video.mp4"
    assert captured["version"] == "v4"
    assert captured["method"] == "GET"
