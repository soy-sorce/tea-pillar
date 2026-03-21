"""Unit tests for the Vertex AI custom endpoint client."""

from __future__ import annotations

from collections.abc import Callable
from types import SimpleNamespace

from google.api_core.exceptions import DeadlineExceeded, GoogleAPICallError, RetryError
from pytest import MonkeyPatch
from src.config import Settings
from src.exceptions import NotConfiguredError, VertexAIError, VertexAITimeoutError
from src.services.cat_model.client import CatModelClient


async def test_predict_raises_when_not_configured() -> None:
    client = CatModelClient(settings=Settings(gcp_project_id="", vertex_endpoint_id=""))

    try:
        await client.predict("image", None, ["video-1"])
    except NotConfiguredError as exc:
        assert exc.error_code == "NOT_CONFIGURED"
    else:
        raise AssertionError("NotConfiguredError was not raised")


async def test_predict_passes_payload_and_parses_response(monkeypatch: MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakeEndpoint:
        def __init__(self, endpoint_name: str, project: str, location: str) -> None:
            captured["endpoint_name"] = endpoint_name
            captured["project"] = project
            captured["location"] = location

        def predict(self, instances: list[dict[str, object]], timeout: int) -> object:
            captured["instances"] = instances
            captured["timeout"] = timeout
            return SimpleNamespace(
                predictions=[
                    {
                        "features": {"emotion_happy": 0.9, "clip_curious_cat": 0.8},
                        "aux_labels": {
                            "emotion_label": "happy",
                            "clip_top_label": "curious_cat",
                            "meow_label": None,
                        },
                        "predicted_rewards": {"video-1": 0.1, "video-2": 0.2},
                    },
                ],
            )

    async def fake_to_thread(
        func: Callable[..., object],
        *args: object,
        **kwargs: object,
    ) -> object:
        return func(*args, **kwargs)

    monkeypatch.setattr("src.services.cat_model.client.aiplatform.Endpoint", FakeEndpoint)
    monkeypatch.setattr("src.services.cat_model.client.asyncio.to_thread", fake_to_thread)
    monkeypatch.setattr(
        "src.services.cat_model.client.VertexImagePreprocessor.preprocess",
        lambda self, image_base64: f"processed-{image_base64}",
    )
    monkeypatch.setattr(
        "src.services.cat_model.client.ModelInputImageUploader.upload_base64_image",
        lambda self, image_base64: f"gs://model-inputs/{image_base64}.jpg",
    )

    client = CatModelClient(
        settings=Settings(
            gcp_project_id="demo-project",
            vertex_endpoint_id="endpoint-id",
            vertex_endpoint_location="asia-northeast1",
            vertex_prediction_timeout=12,
        ),
    )

    response = await client.predict("image-data", "audio-data", ["video-1", "video-2"])

    assert response.emotion_label == "happy"
    assert response.clip_top_label == "curious_cat"
    assert response.meow_label is None
    assert response.predicted_rewards == {"video-1": 0.1, "video-2": 0.2}
    assert captured["instances"] == [
        {
            "image_gcs_uri": "gs://model-inputs/processed-image-data.jpg",
            "audio_base64": "audio-data",
            "candidate_video_ids": ["video-1", "video-2"],
        },
    ]
    assert captured["timeout"] == 12


async def test_predict_maps_deadline_exceeded(monkeypatch: MonkeyPatch) -> None:
    class FakeEndpoint:
        def __init__(self, endpoint_name: str, project: str, location: str) -> None:
            del endpoint_name, project, location

        def predict(self, instances: object, timeout: object) -> object:
            del instances, timeout
            raise DeadlineExceeded("timed out")

    async def fake_to_thread(
        func: Callable[..., object],
        *args: object,
        **kwargs: object,
    ) -> object:
        return func(*args, **kwargs)

    monkeypatch.setattr("src.services.cat_model.client.aiplatform.Endpoint", FakeEndpoint)
    monkeypatch.setattr("src.services.cat_model.client.asyncio.to_thread", fake_to_thread)
    monkeypatch.setattr(
        "src.services.cat_model.client.ModelInputImageUploader.upload_base64_image",
        lambda self, image_base64: "gs://model-inputs/image.jpg",
    )
    client = CatModelClient(settings=Settings(gcp_project_id="demo", vertex_endpoint_id="ep"))

    try:
        await client.predict("image", None, ["video-1"])
    except VertexAITimeoutError as exc:
        assert exc.error_code == "VERTEX_TIMEOUT"
    else:
        raise AssertionError("VertexAITimeoutError was not raised")


async def test_predict_maps_retry_error(monkeypatch: MonkeyPatch) -> None:
    retry_error = RetryError("retry failed", cause=ValueError("cause"))

    class FakeEndpoint:
        def __init__(self, endpoint_name: str, project: str, location: str) -> None:
            del endpoint_name, project, location

        def predict(self, instances: object, timeout: object) -> object:
            del instances, timeout
            raise retry_error

    async def fake_to_thread(
        func: Callable[..., object],
        *args: object,
        **kwargs: object,
    ) -> object:
        return func(*args, **kwargs)

    monkeypatch.setattr("src.services.cat_model.client.aiplatform.Endpoint", FakeEndpoint)
    monkeypatch.setattr("src.services.cat_model.client.asyncio.to_thread", fake_to_thread)
    monkeypatch.setattr(
        "src.services.cat_model.client.ModelInputImageUploader.upload_base64_image",
        lambda self, image_base64: "gs://model-inputs/image.jpg",
    )
    client = CatModelClient(settings=Settings(gcp_project_id="demo", vertex_endpoint_id="ep"))

    try:
        await client.predict("image", None, ["video-1"])
    except VertexAITimeoutError as exc:
        assert exc.error_code == "VERTEX_TIMEOUT"
    else:
        raise AssertionError("VertexAITimeoutError was not raised")


async def test_predict_maps_google_api_call_error(monkeypatch: MonkeyPatch) -> None:
    class FakeEndpoint:
        def __init__(self, endpoint_name: str, project: str, location: str) -> None:
            del endpoint_name, project, location

        def predict(self, instances: object, timeout: object) -> object:
            del instances, timeout
            raise GoogleAPICallError("boom")

    async def fake_to_thread(
        func: Callable[..., object],
        *args: object,
        **kwargs: object,
    ) -> object:
        return func(*args, **kwargs)

    monkeypatch.setattr("src.services.cat_model.client.aiplatform.Endpoint", FakeEndpoint)
    monkeypatch.setattr("src.services.cat_model.client.asyncio.to_thread", fake_to_thread)
    monkeypatch.setattr(
        "src.services.cat_model.client.ModelInputImageUploader.upload_base64_image",
        lambda self, image_base64: "gs://model-inputs/image.jpg",
    )
    client = CatModelClient(settings=Settings(gcp_project_id="demo", vertex_endpoint_id="ep"))

    try:
        await client.predict("image", None, ["video-1"])
    except VertexAIError as exc:
        assert exc.error_code == "VERTEX_FAILED"
    else:
        raise AssertionError("VertexAIError was not raised")
