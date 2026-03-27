"""Unit tests for signed URL generation."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

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
        def __init__(self, project: str, credentials: object | None = None) -> None:
            captured["project"] = project
            captured["credentials"] = credentials

        def bucket(self, bucket_name: str) -> FakeBucket:
            return FakeBucket(bucket_name)

    fake_credentials = SimpleNamespace(
        service_account_email="runtime-sa@example.com",
        token="runtime-token",
        refresh=lambda request: None,
    )
    monkeypatch.setattr(
        "src.services.veo.signed_url.google.auth.default",
        lambda: (fake_credentials, "demo-project"),
    )
    monkeypatch.setattr(
        "src.services.veo.signed_url.StorageClient",
        FakeStorageClient,
    )
    generator = SignedUrlGenerator(
        settings=Settings(
            gcp_project_id="demo-project",
            gcs_signed_url_expiration_hours=3,
            gcs_signing_service_account_file="",
        ),
    )

    url = generator.generate("gs://bucket/path/to/video.mp4")

    assert url == "https://signed.example/video.mp4"
    assert captured["project"] == "demo-project"
    assert captured["bucket_name"] == "bucket"
    assert captured["blob_name"] == "path/to/video.mp4"
    assert captured["version"] == "v4"
    assert captured["method"] == "GET"
    assert captured["service_account_email"] == "runtime-sa@example.com"
    assert captured["access_token"] == "runtime-token"
    assert captured["credentials"] is None


def test_generate_uses_local_service_account_in_development(monkeypatch: MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakeBlob:
        def generate_signed_url(self, **kwargs: object) -> str:
            captured.update(kwargs)
            return "https://signed.example/video.mp4"

    class FakeBucket:
        def blob(self, blob_name: str) -> FakeBlob:
            captured["blob_name"] = blob_name
            return FakeBlob()

    class FakeStorageClient:
        def __init__(self, project: str, credentials: object | None = None) -> None:
            captured["project"] = project
            captured["credentials"] = credentials

        def bucket(self, bucket_name: str) -> FakeBucket:
            captured["bucket_name"] = bucket_name
            return FakeBucket()

    fake_credentials = object()

    def fake_from_service_account_file(path: str) -> object:
        captured["credentials_path"] = path
        return fake_credentials

    monkeypatch.setattr(
        "src.services.veo.signed_url.service_account.Credentials.from_service_account_file",
        fake_from_service_account_file,
    )
    monkeypatch.setattr("src.services.veo.signed_url.StorageClient", FakeStorageClient)
    monkeypatch.setattr("src.services.veo.signed_url.Path.exists", lambda self: True)

    generator = SignedUrlGenerator(
        settings=Settings(
            gcp_project_id="demo-project",
            environment="development",
            gcs_signing_service_account_file="/tmp/key.json",
        ),
    )
    url = generator.generate("gs://bucket/path/to/video.mp4")

    assert url == "https://signed.example/video.mp4"
    assert captured["project"] == "demo-project"
    assert captured["bucket_name"] == "bucket"
    assert captured["blob_name"] == "path/to/video.mp4"
    assert captured["credentials_path"] == "/tmp/key.json"
    assert captured["credentials"] is fake_credentials


def test_generate_raises_when_runtime_credentials_lack_service_account_email(
    monkeypatch: MonkeyPatch,
) -> None:
    fake_credentials = SimpleNamespace(
        service_account_email=None,
        token="runtime-token",
        refresh=lambda request: None,
    )
    monkeypatch.setattr(
        "src.services.veo.signed_url.google.auth.default",
        lambda: (fake_credentials, "demo-project"),
    )

    generator = SignedUrlGenerator(
        settings=Settings(
            gcp_project_id="demo-project",
            environment="prod",
            gcs_signing_service_account_file="",
        ),
    )

    try:
        generator.generate("gs://bucket/path/to/video.mp4")
    except NotConfiguredError as exc:
        assert exc.detail == "runtime credentials do not expose service_account_email"
    else:
        raise AssertionError("NotConfiguredError was not raised")


def test_is_local_signing_mode_returns_false_when_configured_file_is_missing() -> None:
    generator = SignedUrlGenerator(
        settings=Settings(
            gcp_project_id="demo-project",
            environment="development",
            gcs_signing_service_account_file=str(Path("/tmp/missing-key.json")),
        ),
    )

    assert generator._is_local_signing_mode() is False
