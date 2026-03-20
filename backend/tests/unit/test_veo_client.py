"""Unit tests for the Veo client."""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

from google.api_core.exceptions import DeadlineExceeded, GoogleAPICallError, RetryError
from pytest import MonkeyPatch
from src.config import Settings
from src.exceptions import NotConfiguredError, VeoGenerationError, VeoTimeoutError
from src.services.veo.client import VeoClient


async def test_generate_raises_when_not_configured() -> None:
    client = VeoClient(settings=Settings(gcp_project_id="", gcs_bucket_name=""))

    try:
        await client.generate("prompt")
    except NotConfiguredError as exc:
        assert exc.error_code == "NOT_CONFIGURED"
    else:
        raise AssertionError("NotConfiguredError was not raised")


async def test_generate_submits_request_and_polls(monkeypatch: MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakePredictionServiceAsyncClient:
        async def predict(
            self,
            endpoint: str,
            instances: list[dict[str, object]],
            parameters: dict[str, object],
        ) -> object:
            captured["endpoint"] = endpoint
            captured["instances"] = instances
            captured["parameters"] = parameters
            return SimpleNamespace(operation=SimpleNamespace(name="operation-1"))

    async def fake_poll(self: Any, operation_name: str) -> str:
        captured["operation_name"] = operation_name
        return "gs://bucket/generated/video.mp4"

    monkeypatch.setattr(
        "src.services.veo.client.vertexai.init", lambda **kwargs: captured.update(kwargs)
    )
    monkeypatch.setattr(
        "src.services.veo.client.aiplatform_v1.PredictionServiceAsyncClient",
        FakePredictionServiceAsyncClient,
    )
    monkeypatch.setattr("src.services.veo.client.VeoClient._poll_until_done", fake_poll)

    client = VeoClient(settings=Settings(gcp_project_id="demo", gcs_bucket_name="bucket"))
    uri = await client.generate("final prompt")

    assert uri == "gs://bucket/generated/video.mp4"
    assert captured["project"] == "demo"
    assert captured["location"] == "asia-northeast1"
    assert "publishers/google/models" in str(captured["endpoint"])
    assert captured["instances"] == [{"prompt": "final prompt"}]
    assert captured["parameters"] == {
        "generate_audio": False,
        "output_gcs_uri": "gs://bucket/",
    }
    assert captured["operation_name"] == "operation-1"


async def test_generate_maps_deadline_exceeded(monkeypatch: MonkeyPatch) -> None:
    class FakePredictionServiceAsyncClient:
        async def predict(self, endpoint: object, instances: object, parameters: object) -> object:
            del endpoint, instances, parameters
            raise DeadlineExceeded("timed out")

    monkeypatch.setattr("src.services.veo.client.vertexai.init", lambda **kwargs: None)
    monkeypatch.setattr(
        "src.services.veo.client.aiplatform_v1.PredictionServiceAsyncClient",
        FakePredictionServiceAsyncClient,
    )
    client = VeoClient(settings=Settings(gcp_project_id="demo", gcs_bucket_name="bucket"))

    try:
        await client.generate("prompt")
    except VeoTimeoutError as exc:
        assert exc.error_code == "VEO_TIMEOUT"
    else:
        raise AssertionError("VeoTimeoutError was not raised")


async def test_generate_maps_retry_error(monkeypatch: MonkeyPatch) -> None:
    retry_error = RetryError("timed out", cause=ValueError("cause"))

    class FakePredictionServiceAsyncClient:
        async def predict(self, endpoint: object, instances: object, parameters: object) -> object:
            del endpoint, instances, parameters
            raise retry_error

    monkeypatch.setattr("src.services.veo.client.vertexai.init", lambda **kwargs: None)
    monkeypatch.setattr(
        "src.services.veo.client.aiplatform_v1.PredictionServiceAsyncClient",
        FakePredictionServiceAsyncClient,
    )
    client = VeoClient(settings=Settings(gcp_project_id="demo", gcs_bucket_name="bucket"))

    try:
        await client.generate("prompt")
    except VeoTimeoutError as exc:
        assert exc.error_code == "VEO_TIMEOUT"
    else:
        raise AssertionError("VeoTimeoutError was not raised")


async def test_generate_maps_google_api_error(monkeypatch: MonkeyPatch) -> None:
    class FakePredictionServiceAsyncClient:
        async def predict(self, endpoint: object, instances: object, parameters: object) -> object:
            del endpoint, instances, parameters
            raise GoogleAPICallError("boom")

    monkeypatch.setattr("src.services.veo.client.vertexai.init", lambda **kwargs: None)
    monkeypatch.setattr(
        "src.services.veo.client.aiplatform_v1.PredictionServiceAsyncClient",
        FakePredictionServiceAsyncClient,
    )
    client = VeoClient(settings=Settings(gcp_project_id="demo", gcs_bucket_name="bucket"))

    try:
        await client.generate("prompt")
    except VeoGenerationError as exc:
        assert exc.error_code == "VEO_FAILED"
    else:
        raise AssertionError("VeoGenerationError was not raised")


async def test_poll_until_done_returns_gcs_uri(monkeypatch: MonkeyPatch) -> None:
    operations = [
        SimpleNamespace(done=False),
        SimpleNamespace(
            done=True,
            error=SimpleNamespace(code=0, message=""),
            response=SimpleNamespace(value=b'{"gcs_uri":"gs://bucket/video.mp4"}'),
        ),
    ]

    class FakeOperationsAsyncClient:
        async def get_operation(self, name: str) -> object:
            assert name == "operation-1"
            return operations.pop(0)

    async def fake_sleep(seconds: float) -> None:
        del seconds

    monkeypatch.setattr(
        "src.services.veo.client.aiplatform_v1.OperationsAsyncClient",
        FakeOperationsAsyncClient,
        raising=False,
    )
    monkeypatch.setattr("src.services.veo.client.asyncio.sleep", fake_sleep)

    client = VeoClient(settings=Settings(veo_timeout=10, veo_polling_interval=0))
    result = await client._poll_until_done("operation-1")

    assert result == "gs://bucket/video.mp4"


async def test_poll_until_done_raises_on_operation_error(monkeypatch: MonkeyPatch) -> None:
    class FakeOperationsAsyncClient:
        async def get_operation(self, name: str) -> object:
            del name
            return SimpleNamespace(
                done=True,
                error=SimpleNamespace(code=1, message="failed"),
                response=SimpleNamespace(value=b""),
            )

    monkeypatch.setattr(
        "src.services.veo.client.aiplatform_v1.OperationsAsyncClient",
        FakeOperationsAsyncClient,
        raising=False,
    )

    client = VeoClient(settings=Settings(veo_timeout=10))

    try:
        await client._poll_until_done("operation-1")
    except VeoGenerationError as exc:
        assert exc.detail == "failed"
    else:
        raise AssertionError("VeoGenerationError was not raised")


async def test_poll_until_done_raises_timeout(monkeypatch: MonkeyPatch) -> None:
    class FakeOperationsAsyncClient:
        async def get_operation(self, name: str) -> object:
            del name
            return SimpleNamespace(done=False)

    calls = {"count": 0}

    async def fake_sleep(seconds: float) -> None:
        del seconds

    def fake_monotonic() -> float:
        calls["count"] += 1
        return 0.0 if calls["count"] == 1 else 1.5

    monkeypatch.setattr(
        "src.services.veo.client.aiplatform_v1.OperationsAsyncClient",
        FakeOperationsAsyncClient,
        raising=False,
    )
    monkeypatch.setattr("src.services.veo.client.time.monotonic", fake_monotonic)
    monkeypatch.setattr("src.services.veo.client.asyncio.sleep", fake_sleep)

    client = VeoClient(settings=Settings(veo_timeout=1, veo_polling_interval=0))

    try:
        await client._poll_until_done("operation-1")
    except VeoTimeoutError as exc:
        assert exc.error_code == "VEO_TIMEOUT"
    else:
        raise AssertionError("VeoTimeoutError was not raised")


def test_extract_gcs_uri_supports_multiple_formats() -> None:
    client = VeoClient(settings=Settings())

    assert client._extract_gcs_uri(b"gs://bucket/raw.mp4") == "gs://bucket/raw.mp4"
    assert (
        client._extract_gcs_uri(json.dumps({"gcs_uri": "gs://bucket/a.mp4"}).encode())
        == "gs://bucket/a.mp4"
    )
    assert (
        client._extract_gcs_uri(json.dumps({"output_gcs_uri": "gs://bucket/b.mp4"}).encode())
        == "gs://bucket/b.mp4"
    )
    assert (
        client._extract_gcs_uri(json.dumps({"uri": "gs://bucket/c.mp4"}).encode())
        == "gs://bucket/c.mp4"
    )
    assert (
        client._extract_gcs_uri(
            json.dumps({"artifacts": [{"gcs_uri": "gs://bucket/d.mp4"}]}).encode(),
        )
        == "gs://bucket/d.mp4"
    )


def test_extract_gcs_uri_raises_for_unknown_format() -> None:
    client = VeoClient(settings=Settings())

    try:
        client._extract_gcs_uri(b'{"unexpected":"value"}')
    except VeoGenerationError as exc:
        assert exc.error_code == "VEO_FAILED"
    else:
        raise AssertionError("VeoGenerationError was not raised")
