"""Route-level tests for POST /feedback."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from src.app import create_app
from src.config import Settings, get_settings
from src.exceptions import FirestoreError, ResourceNotFoundError
from src.models.firestore import SessionDocument


@dataclass
class FakeFirestore:
    session: SessionDocument
    saved_feedback: tuple[str, str, str, float] | None = None

    async def get_session(self: Self, session_id: str) -> SessionDocument:
        assert session_id == self.session.session_id
        return self.session

    async def save_feedback(
        self: Self,
        session_id: str,
        template_id: str,
        reaction: str,
        reward: float,
    ) -> None:
        self.saved_feedback = (session_id, template_id, reaction, reward)


@dataclass
class FakeBandit:
    updated: tuple[str, str, float] | None = None

    async def update(self: Self, template_id: str, state_key: str, reward: float) -> None:
        self.updated = (template_id, state_key, reward)


def test_feedback_updates_bandit_and_persists_payload(monkeypatch: MonkeyPatch) -> None:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings()

    firestore = FakeFirestore(
        session=SessionDocument(
            session_id="session-1",
            mode="experience",
            status="done",
            template_id="video-1",
            state_key="unknown_happy_curious_cat",
        ),
    )
    bandit = FakeBandit()

    monkeypatch.setattr("src.routers.feedback.FirestoreClient", lambda settings: firestore)
    monkeypatch.setattr(
        "src.routers.feedback.UCBBandit",
        lambda settings, firestore_client: bandit,
    )

    client = TestClient(app)
    response = client.post(
        "/feedback",
        json={"session_id": "session-1", "reaction": "good"},
    )

    assert response.status_code == 200
    assert response.json() == {"reward": 1.0, "updated_template_id": "video-1"}
    assert firestore.saved_feedback == ("session-1", "video-1", "good", 1.0)
    assert bandit.updated == ("video-1", "unknown_happy_curious_cat", 1.0)


def test_feedback_returns_409_for_non_done_session(monkeypatch: MonkeyPatch) -> None:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings()

    firestore = FakeFirestore(
        session=SessionDocument(
            session_id="session-1",
            mode="experience",
            status="generating",
            template_id="video-1",
            state_key="unknown_happy_curious_cat",
        ),
    )
    bandit = FakeBandit()

    monkeypatch.setattr("src.routers.feedback.FirestoreClient", lambda settings: firestore)
    monkeypatch.setattr(
        "src.routers.feedback.UCBBandit",
        lambda settings, firestore_client: bandit,
    )

    client = TestClient(app)
    response = client.post(
        "/feedback",
        json={"session_id": "session-1", "reaction": "good"},
    )

    assert response.status_code == 409
    assert response.json()["error_code"] == "SESSION_CONFLICT"
    assert firestore.saved_feedback is None
    assert bandit.updated is None


@pytest.mark.parametrize(
    ("reaction", "reward"),
    [("neutral", 0.0), ("bad", -0.5)],
)
def test_feedback_reward_mapping(monkeypatch: MonkeyPatch, reaction: str, reward: float) -> None:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings()

    firestore = FakeFirestore(
        session=SessionDocument(
            session_id="session-1",
            mode="experience",
            status="done",
            template_id="video-1",
            state_key="unknown_happy_curious_cat",
        ),
    )
    bandit = FakeBandit()

    monkeypatch.setattr("src.routers.feedback.FirestoreClient", lambda settings: firestore)
    monkeypatch.setattr("src.routers.feedback.UCBBandit", lambda settings, firestore_client: bandit)

    client = TestClient(app)
    response = client.post("/feedback", json={"session_id": "session-1", "reaction": reaction})

    assert response.status_code == 200
    assert response.json() == {"reward": reward, "updated_template_id": "video-1"}


def test_feedback_returns_404_when_session_missing(monkeypatch: MonkeyPatch) -> None:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings()

    class MissingSessionFirestore(FakeFirestore):
        async def get_session(self: Self, session_id: str) -> SessionDocument:
            del session_id
            raise ResourceNotFoundError(detail="missing")

    monkeypatch.setattr(
        "src.routers.feedback.FirestoreClient",
        lambda settings: MissingSessionFirestore(
            session=SessionDocument(session_id="x", mode="experience", status="done")
        ),
    )
    monkeypatch.setattr(
        "src.routers.feedback.UCBBandit", lambda settings, firestore_client: FakeBandit()
    )

    client = TestClient(app)
    response = client.post("/feedback", json={"session_id": "session-1", "reaction": "good"})

    assert response.status_code == 404
    assert response.json()["error_code"] == "NOT_FOUND"


@pytest.mark.parametrize(
    "field_name",
    ["template_id", "state_key"],
)
def test_feedback_returns_409_when_session_data_missing(
    monkeypatch: MonkeyPatch,
    field_name: str,
) -> None:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings()

    session = SessionDocument(
        session_id="session-1",
        mode="experience",
        status="done",
        template_id="video-1",
        state_key="unknown_happy_curious_cat",
    )
    if field_name == "template_id":
        session.template_id = None
    else:
        session.state_key = None
    firestore = FakeFirestore(session=session)

    monkeypatch.setattr("src.routers.feedback.FirestoreClient", lambda settings: firestore)
    monkeypatch.setattr(
        "src.routers.feedback.UCBBandit", lambda settings, firestore_client: FakeBandit()
    )

    client = TestClient(app)
    response = client.post("/feedback", json={"session_id": "session-1", "reaction": "good"})

    assert response.status_code == 409
    assert response.json()["error_code"] == "SESSION_CONFLICT"


def test_feedback_returns_500_when_save_feedback_fails(monkeypatch: MonkeyPatch) -> None:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings()

    class FailingFirestore(FakeFirestore):
        async def save_feedback(
            self: Self,
            session_id: str,
            template_id: str,
            reaction: str,
            reward: float,
        ) -> None:
            del session_id, template_id, reaction, reward
            raise FirestoreError(detail="write failed")

    firestore = FailingFirestore(
        session=SessionDocument(
            session_id="session-1",
            mode="experience",
            status="done",
            template_id="video-1",
            state_key="unknown_happy_curious_cat",
        ),
    )

    monkeypatch.setattr("src.routers.feedback.FirestoreClient", lambda settings: firestore)
    monkeypatch.setattr(
        "src.routers.feedback.UCBBandit", lambda settings, firestore_client: FakeBandit()
    )

    client = TestClient(app, raise_server_exceptions=False)
    response = client.post("/feedback", json={"session_id": "session-1", "reaction": "good"})

    assert response.status_code == 500
    assert response.json()["error_code"] == "FIRESTORE_FAILED"


def test_feedback_returns_500_when_bandit_update_fails(monkeypatch: MonkeyPatch) -> None:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings()

    class FailingBandit(FakeBandit):
        async def update(self: Self, template_id: str, state_key: str, reward: float) -> None:
            del template_id, state_key, reward
            raise FirestoreError(detail="update failed")

    firestore = FakeFirestore(
        session=SessionDocument(
            session_id="session-1",
            mode="experience",
            status="done",
            template_id="video-1",
            state_key="unknown_happy_curious_cat",
        ),
    )

    monkeypatch.setattr("src.routers.feedback.FirestoreClient", lambda settings: firestore)
    monkeypatch.setattr(
        "src.routers.feedback.UCBBandit", lambda settings, firestore_client: FailingBandit()
    )

    client = TestClient(app, raise_server_exceptions=False)
    response = client.post("/feedback", json={"session_id": "session-1", "reaction": "good"})

    assert response.status_code == 500
    assert response.json()["error_code"] == "FIRESTORE_FAILED"


def test_feedback_rejects_invalid_reaction_payload() -> None:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings()

    client = TestClient(app)
    response = client.post("/feedback", json={"session_id": "session-1", "reaction": "wow"})

    assert response.status_code == 400
    assert response.json()["error_code"] == "INVALID_INPUT"
