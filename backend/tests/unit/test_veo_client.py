"""Unit tests for the Veo client."""

from __future__ import annotations

from types import SimpleNamespace
from typing import cast

from google.api_core.exceptions import DeadlineExceeded, GoogleAPICallError, RetryError
from pytest import MonkeyPatch
from src.clients.veo import VeoClient
from src.config import Settings
from src.exceptions import NotConfiguredError, VeoGenerationError, VeoTimeoutError


def _operation(*, done: bool, uri: str | None = None, error: object | None = None) -> object:
    generated_videos = [SimpleNamespace(video=SimpleNamespace(uri=uri))] if uri else None
    response = SimpleNamespace(generated_videos=generated_videos) if generated_videos else None
    return SimpleNamespace(
        done=done,
        name="operation-1",
        error=error,
        result=response,
        response=response,
    )


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

    class FakeModels:
        def generate_videos(self, *, model: str, prompt: str, config: object) -> object:
            captured["model"] = model
            captured["prompt"] = prompt
            captured["config"] = config
            return _operation(done=False)

    class FakeOperations:
        def get(self, operation: object) -> object:
            captured["operation_name"] = getattr(operation, "name", None)
            return _operation(done=True, uri="gs://bucket/generated/video.mp4")

    class FakeClient:
        def __init__(self, *, vertexai: bool, project: str, location: str) -> None:
            captured["vertexai"] = vertexai
            captured["project"] = project
            captured["location"] = location
            self.models = FakeModels()
            self.operations = FakeOperations()

    async def fake_sleep(seconds: float) -> None:
        del seconds

    monkeypatch.setattr("src.clients.veo.vertexai.init", lambda **kwargs: captured.update(kwargs))
    monkeypatch.setattr("src.clients.veo.Client", FakeClient)
    monkeypatch.setattr("src.clients.veo.asyncio.sleep", fake_sleep)

    client = VeoClient(
        settings=Settings(
            gcp_project_id="demo",
            gcs_bucket_name="bucket",
            veo_polling_interval=0,
        )
    )
    uri = await client.generate("final prompt")

    assert uri == "gs://bucket/generated/video.mp4"
    assert captured["project"] == "demo"
    assert captured["location"] == "global"
    assert captured["vertexai"] is True
    assert captured["model"] == "veo-3.1-fast-generate-001"
    assert captured["prompt"] == "final prompt"
    config = cast(SimpleNamespace, captured["config"])
    assert config.generate_audio is False
    assert config.output_gcs_uri == "gs://bucket/"
    assert config.duration_seconds == 8
    assert captured["operation_name"] == "operation-1"


async def test_generate_maps_deadline_exceeded(monkeypatch: MonkeyPatch) -> None:
    class FakeModels:
        def generate_videos(self, *, model: str, prompt: str, config: object) -> object:
            del model, prompt, config
            raise DeadlineExceeded("timed out")

    class FakeClient:
        def __init__(self, *, vertexai: bool, project: str, location: str) -> None:
            del vertexai, project, location
            self.models = FakeModels()
            self.operations = SimpleNamespace()

    monkeypatch.setattr("src.clients.veo.vertexai.init", lambda **kwargs: None)
    monkeypatch.setattr("src.clients.veo.Client", FakeClient)
    client = VeoClient(settings=Settings(gcp_project_id="demo", gcs_bucket_name="bucket"))

    try:
        await client.generate("prompt")
    except VeoTimeoutError as exc:
        assert exc.error_code == "VEO_TIMEOUT"
    else:
        raise AssertionError("VeoTimeoutError was not raised")


async def test_generate_maps_retry_error(monkeypatch: MonkeyPatch) -> None:
    retry_error = RetryError("timed out", cause=ValueError("cause"))

    class FakeModels:
        def generate_videos(self, *, model: str, prompt: str, config: object) -> object:
            del model, prompt, config
            raise retry_error

    class FakeClient:
        def __init__(self, *, vertexai: bool, project: str, location: str) -> None:
            del vertexai, project, location
            self.models = FakeModels()
            self.operations = SimpleNamespace()

    monkeypatch.setattr("src.clients.veo.vertexai.init", lambda **kwargs: None)
    monkeypatch.setattr("src.clients.veo.Client", FakeClient)
    client = VeoClient(settings=Settings(gcp_project_id="demo", gcs_bucket_name="bucket"))

    try:
        await client.generate("prompt")
    except VeoTimeoutError as exc:
        assert exc.error_code == "VEO_TIMEOUT"
    else:
        raise AssertionError("VeoTimeoutError was not raised")


async def test_generate_maps_google_api_error(monkeypatch: MonkeyPatch) -> None:
    class FakeModels:
        def generate_videos(self, *, model: str, prompt: str, config: object) -> object:
            del model, prompt, config
            raise GoogleAPICallError("boom")

    class FakeClient:
        def __init__(self, *, vertexai: bool, project: str, location: str) -> None:
            del vertexai, project, location
            self.models = FakeModels()
            self.operations = SimpleNamespace()

    monkeypatch.setattr("src.clients.veo.vertexai.init", lambda **kwargs: None)
    monkeypatch.setattr("src.clients.veo.Client", FakeClient)
    client = VeoClient(settings=Settings(gcp_project_id="demo", gcs_bucket_name="bucket"))

    try:
        await client.generate("prompt")
    except VeoGenerationError as exc:
        assert exc.error_code == "VEO_FAILED"
    else:
        raise AssertionError("VeoGenerationError was not raised")


async def test_poll_until_done_returns_gcs_uri(monkeypatch: MonkeyPatch) -> None:
    operations = [
        _operation(done=False),
        _operation(done=True, uri="gs://bucket/video.mp4"),
    ]

    class FakeOperations:
        def get(self, operation: object) -> object:
            assert getattr(operation, "name", None) == "operation-1"
            return operations.pop(0)

    class FakeClient:
        def __init__(self) -> None:
            self.operations = FakeOperations()

    async def fake_sleep(seconds: float) -> None:
        del seconds

    monkeypatch.setattr("src.clients.veo.asyncio.sleep", fake_sleep)

    client = VeoClient(settings=Settings(veo_timeout=10, veo_polling_interval=0))
    result = await client._poll_until_done(FakeClient(), _operation(done=False))

    assert result == "gs://bucket/video.mp4"


async def test_poll_until_done_raises_on_operation_error(monkeypatch: MonkeyPatch) -> None:
    class FakeOperations:
        def get(self, operation: object) -> object:
            del operation
            return _operation(
                done=True,
                error=SimpleNamespace(code=1, message="failed"),
            )

    class FakeClient:
        def __init__(self) -> None:
            self.operations = FakeOperations()

    client = VeoClient(settings=Settings(veo_timeout=10))

    try:
        await client._poll_until_done(FakeClient(), _operation(done=False))
    except VeoGenerationError as exc:
        assert exc.detail == "failed"
    else:
        raise AssertionError("VeoGenerationError was not raised")


async def test_poll_until_done_raises_timeout(monkeypatch: MonkeyPatch) -> None:
    class FakeOperations:
        def get(self, operation: object) -> object:
            del operation
            return _operation(done=False)

    class FakeClient:
        def __init__(self) -> None:
            self.operations = FakeOperations()

    calls = {"count": 0}

    async def fake_sleep(seconds: float) -> None:
        del seconds

    def fake_monotonic() -> float:
        calls["count"] += 1
        return 0.0 if calls["count"] == 1 else 1.5

    monkeypatch.setattr("src.clients.veo.time.monotonic", fake_monotonic)
    monkeypatch.setattr("src.clients.veo.asyncio.sleep", fake_sleep)

    client = VeoClient(settings=Settings(veo_timeout=1, veo_polling_interval=0))

    try:
        await client._poll_until_done(FakeClient(), _operation(done=False))
    except VeoTimeoutError as exc:
        assert exc.error_code == "VEO_TIMEOUT"
    else:
        raise AssertionError("VeoTimeoutError was not raised")


def test_extract_gcs_uri_supports_sdk_response() -> None:
    client = VeoClient(settings=Settings())
    operation = _operation(done=True, uri="gs://bucket/video.mp4")

    assert client._extract_gcs_uri(operation) == "gs://bucket/video.mp4"


def test_extract_gcs_uri_raises_for_unknown_format() -> None:
    client = VeoClient(settings=Settings())
    operation = _operation(done=True)

    try:
        client._extract_gcs_uri(operation)
    except VeoGenerationError as exc:
        assert exc.error_code == "VEO_FAILED"
    else:
        raise AssertionError("VeoGenerationError was not raised")
