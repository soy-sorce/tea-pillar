"""Integration tests for app-level routes and handlers."""

from __future__ import annotations

from fastapi.testclient import TestClient
from src.app import create_app
from src.config import Settings, get_settings
from src.exceptions import FirestoreError


def test_root_and_health_routes_return_expected_payload() -> None:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(environment="test")
    client = TestClient(app)

    root_response = client.get("/")
    health_response = client.get("/health")

    assert root_response.status_code == 200
    assert root_response.json() == {
        "service": "nekkoflix-backend",
        "status": "ok",
        "environment": "test",
    }
    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok", "environment": "test"}


def test_favicon_returns_204() -> None:
    client = TestClient(create_app())

    response = client.get("/favicon.ico")

    assert response.status_code == 204


def test_middleware_adds_request_id_header() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]


def test_invalid_payload_returns_400() -> None:
    client = TestClient(create_app())

    response = client.post("/generate", json={"mode": "experience", "image_base64": ""})

    assert response.status_code == 400
    assert response.json()["error_code"] == "INVALID_INPUT"


def test_custom_application_error_is_serialized() -> None:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings()

    class FailingGenerateOrchestrator:
        def __init__(self, settings: Settings) -> None:
            del settings

        async def execute(self, request: object) -> object:
            del request
            raise FirestoreError(detail="boom")

    from pytest import MonkeyPatch

    monkeypatch = MonkeyPatch()
    monkeypatch.setattr("src.routers.generate.GenerateOrchestrator", FailingGenerateOrchestrator)

    try:
        client = TestClient(app, raise_server_exceptions=False)
        response = client.post("/generate", json={"mode": "experience", "image_base64": "encoded"})
    finally:
        monkeypatch.undo()

    assert response.status_code == 500
    assert response.json() == {
        "error_code": "FIRESTORE_FAILED",
        "message": "データの保存または取得に失敗しました",
    }
