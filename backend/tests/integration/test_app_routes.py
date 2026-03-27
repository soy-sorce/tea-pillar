"""Integration tests for app-level routes and handlers."""

from __future__ import annotations

from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from src.app import create_app
from src.config import Settings, get_settings
from src.dependencies import get_generate_orchestrator
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


def test_cors_allows_configured_frontend_origin() -> None:
    monkeypatch = MonkeyPatch()
    monkeypatch.setattr(
        "src.app.get_settings",
        lambda: Settings(
            environment="test",
            frontend_origin="https://frontend.example.com",
        ),
    )

    try:
        app = create_app()
    finally:
        monkeypatch.undo()

    client = TestClient(app)

    response = client.options(
        "/generate",
        headers={
            "Origin": "https://frontend.example.com",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://frontend.example.com"


def test_default_frontend_origin_is_localhost_for_safer_local_fallback() -> None:
    settings = Settings(
        environment="test",
    )
    assert settings.frontend_origin == "http://localhost:5173"


def test_invalid_payload_returns_400() -> None:
    client = TestClient(create_app())

    response = client.post("/generate", json={"mode": "experience", "image_base64": ""})

    assert response.status_code == 400
    assert response.json()["error_code"] == "INVALID_INPUT"


def test_custom_application_error_is_serialized() -> None:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings()

    class FailingGenerateOrchestrator:
        async def execute(self, request: object) -> object:
            del request
            raise FirestoreError(detail="boom")

    app.dependency_overrides[get_generate_orchestrator] = lambda: FailingGenerateOrchestrator()
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post("/generate", json={"mode": "experience", "image_base64": "encoded"})

    assert response.status_code == 500
    assert response.json() == {
        "error_code": "FIRESTORE_FAILED",
        "message": "データの保存または取得に失敗しました",
    }
