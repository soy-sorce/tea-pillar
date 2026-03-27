"""Route-level tests for reaction upload APIs."""

from __future__ import annotations

from typing import cast

from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from src.app import create_app
from src.config import Settings, get_settings
from src.models.firestore import SessionDocument
from src.models.request import RewardAnalysisTaskRequest


def test_reaction_upload_url_route_returns_signed_url(monkeypatch: MonkeyPatch) -> None:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(
        environment="test",
        reaction_video_upload_url_expires_seconds=900,
    )

    class FakeFirestoreClient:
        def __init__(self, settings: Settings) -> None:
            del settings

        async def get_session(self, session_id: str) -> SessionDocument:
            return SessionDocument(
                session_id=session_id,
                mode="production",
                status="generated",
                reward_status="not_started",
                template_id="video-1",
                state_key="unknown_happy_curious_cat",
            )

    class FakeReactionVideoStorageService:
        def __init__(self, settings: Settings) -> None:
            del settings

        def issue_upload_url(self, *, session_id: str) -> tuple[str, str]:
            return (
                "https://signed.example/upload",
                f"gs://reaction-bucket/reaction_videos/{session_id}/upload.mp4",
            )

    monkeypatch.setattr("src.routers.reaction.FirestoreClient", FakeFirestoreClient)
    monkeypatch.setattr(
        "src.routers.reaction.ReactionVideoStorageService",
        FakeReactionVideoStorageService,
    )

    client = TestClient(app)
    response = client.post("/sessions/session-1/reaction-upload-url")

    assert response.status_code == 200
    assert response.json() == {
        "session_id": "session-1",
        "upload_url": "https://signed.example/upload",
        "reaction_video_gcs_uri": "gs://reaction-bucket/reaction_videos/session-1/upload.mp4",
        "expires_in_seconds": 900,
    }


def test_reaction_complete_route_registers_uri_and_starts_background_task(
    monkeypatch: MonkeyPatch,
) -> None:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(environment="test")
    calls: dict[str, object] = {}

    class FakeFirestoreClient:
        def __init__(self, settings: Settings) -> None:
            del settings

        async def get_session(self, session_id: str) -> SessionDocument:
            return SessionDocument(
                session_id=session_id,
                mode="production",
                status="generated",
                reward_status="not_started",
                template_id="video-1",
                state_key="unknown_happy_curious_cat",
            )

        async def attach_reaction_video(
            self,
            *,
            session_id: str,
            reaction_video_gcs_uri: str,
        ) -> None:
            calls["session_id"] = session_id
            calls["reaction_video_gcs_uri"] = reaction_video_gcs_uri

    class FakeReactionVideoStorageService:
        def __init__(self, settings: Settings) -> None:
            del settings

        def validate_gcs_uri(self, *, session_id: str, reaction_video_gcs_uri: str) -> str:
            calls["validated_session_id"] = session_id
            return reaction_video_gcs_uri

    class FakeRewardAnalysisService:
        def __init__(self, settings: Settings) -> None:
            del settings

        async def analyze(self, payload: object) -> None:
            calls["background_payload"] = payload

    monkeypatch.setattr("src.routers.reaction.FirestoreClient", FakeFirestoreClient)
    monkeypatch.setattr(
        "src.routers.reaction.ReactionVideoStorageService",
        FakeReactionVideoStorageService,
    )
    monkeypatch.setattr("src.routers.reaction.RewardAnalysisService", FakeRewardAnalysisService)

    client = TestClient(app)
    response = client.post(
        "/sessions/session-1/reaction",
        json={
            "reaction_video_gcs_uri": "gs://reaction-bucket/reaction_videos/session-1/upload.mp4",
        },
    )

    assert response.status_code == 202
    assert response.json() == {
        "session_id": "session-1",
        "status": "accepted",
        "reaction_video_gcs_uri": "gs://reaction-bucket/reaction_videos/session-1/upload.mp4",
    }
    assert calls["session_id"] == "session-1"
    assert calls["validated_session_id"] == "session-1"
    background_payload = cast(RewardAnalysisTaskRequest, calls["background_payload"])
    assert background_payload.template_id == "video-1"
    assert background_payload.state_key == "unknown_happy_curious_cat"
