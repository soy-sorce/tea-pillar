"""Route-level tests for POST /generate."""

from __future__ import annotations

from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from src.app import create_app
from src.dependencies import get_generate_orchestrator
from src.exceptions import GeminiError
from src.models.request import GenerateRequest
from src.models.response import GenerateResponse


def test_generate_route_returns_happy_path_payload(monkeypatch: MonkeyPatch) -> None:
    app = create_app()
    captured: dict[str, object] = {}

    class FakeOrchestrator:
        async def execute(self, request: GenerateRequest) -> GenerateResponse:
            captured["request"] = request
            return GenerateResponse(
                session_id="session-1",
                video_url="https://signed.example/video.mp4",
                state_key="unknown_happy_curious_cat",
                template_id="video-1",
                template_name="mouse chase",
            )

    app.dependency_overrides[get_generate_orchestrator] = lambda: FakeOrchestrator()

    client = TestClient(app)
    response = client.post(
        "/generate",
        json={
            "mode": "experience",
            "image_base64": "encoded-image",
            "audio_base64": None,
            "user_context": "curious",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "session_id": "session-1",
        "video_url": "https://signed.example/video.mp4",
        "state_key": "unknown_happy_curious_cat",
        "template_id": "video-1",
        "template_name": "mouse chase",
    }
    assert captured["request"] == GenerateRequest(
        mode="experience",
        image_base64="encoded-image",
        audio_base64=None,
        user_context="curious",
    )


def test_generate_route_propagates_application_error(monkeypatch: MonkeyPatch) -> None:
    app = create_app()

    class FailingOrchestrator:
        async def execute(self, request: GenerateRequest) -> GenerateResponse:
            del request
            raise GeminiError(detail="gemini failed")

    app.dependency_overrides[get_generate_orchestrator] = lambda: FailingOrchestrator()

    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/generate",
        json={"mode": "experience", "image_base64": "encoded-image"},
    )

    assert response.status_code == 502
    assert response.json()["error_code"] == "GEMINI_FAILED"
