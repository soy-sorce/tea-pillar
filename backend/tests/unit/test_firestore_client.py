"""Unit tests for FirestoreClient."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass

from google.api_core.exceptions import GoogleAPICallError
from pytest import MonkeyPatch
from src.config import Settings
from src.exceptions import FirestoreError, ResourceNotFoundError
from src.models.internal import BanditSelection, GenerationContext
from src.services.firestore.client import FirestoreClient


@dataclass
class FakeSnapshot:
    payload: dict[str, object] | None
    exists: bool = True

    def to_dict(self) -> dict[str, object] | None:
        return self.payload


class FakeStream:
    def __init__(self, snapshots: list[FakeSnapshot]) -> None:
        self._snapshots = snapshots

    def __aiter__(self) -> AsyncIterator[FakeSnapshot]:
        self._iter = iter(self._snapshots)
        return self

    async def __anext__(self) -> FakeSnapshot:
        try:
            return next(self._iter)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


class FakeDocumentReference:
    def __init__(self, collection: FakeCollection, document_id: str) -> None:
        self.collection = collection
        self.document_id = document_id

    async def set(self, payload: dict[str, object]) -> None:
        self.collection.documents[self.document_id] = payload

    async def update(self, payload: dict[str, object]) -> None:
        current = self.collection.documents.get(self.document_id, {})
        current.update(payload)
        self.collection.documents[self.document_id] = current

    async def get(self, transaction: object = None) -> FakeSnapshot:
        del transaction
        payload = self.collection.documents.get(self.document_id)
        return FakeSnapshot(payload, exists=payload is not None)


class FakeCollection:
    def __init__(self, documents: dict[str, dict[str, object]]) -> None:
        self.documents = documents

    def document(self, document_id: str) -> FakeDocumentReference:
        return FakeDocumentReference(self, document_id)

    def where(self, field_name: str, op: str, value: object) -> FakeQuery:
        del op
        return FakeQuery(self.documents, field_name, value)

    def stream(self) -> FakeStream:
        return FakeStream([FakeSnapshot(payload) for payload in self.documents.values()])


class FakeQuery:
    def __init__(
        self, documents: dict[str, dict[str, object]], field_name: str, value: object
    ) -> None:
        self.documents = documents
        self.field_name = field_name
        self.value = value

    def stream(self) -> FakeStream:
        snapshots = [
            FakeSnapshot(payload)
            for payload in self.documents.values()
            if payload.get(self.field_name) == self.value
        ]
        return FakeStream(snapshots)


class FakeTransaction:
    def set(self, document_ref: FakeDocumentReference, payload: dict[str, object]) -> None:
        document_ref.collection.documents[document_ref.document_id] = payload


class FakeAsyncClient:
    def __init__(self, project: str | None = None, database: str | None = None) -> None:
        del project, database
        self.collections: dict[str, FakeCollection] = {
            "sessions": FakeCollection({}),
            "bandit_table": FakeCollection({}),
            "templates": FakeCollection({}),
            "feedbacks": FakeCollection({}),
        }

    def collection(self, name: str) -> FakeCollection:
        return self.collections[name]

    def transaction(self) -> FakeTransaction:
        return FakeTransaction()


def _make_client(monkeypatch: MonkeyPatch) -> FirestoreClient:
    monkeypatch.setattr("src.services.firestore.client.firestore.AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(
        "src.services.firestore.client.firestore.async_transactional",
        lambda fn: fn,
    )
    monkeypatch.setattr("src.services.firestore.client.firestore.SERVER_TIMESTAMP", "SERVER_TS")
    return FirestoreClient(settings=Settings(gcp_project_id="demo"))


async def test_create_complete_and_fail_session(monkeypatch: MonkeyPatch) -> None:
    client = _make_client(monkeypatch)
    ctx = GenerationContext(
        session_id="session-1",
        mode="experience",
        image_base64="image",
        audio_base64=None,
        user_context="curious",
        state_key="unknown_happy_curious_cat",
        bandit_selection=BanditSelection(
            template_id="video-1",
            template_name="template",
            prompt_text="prompt",
            predicted_reward=0.1,
            ucb_bonus=0.2,
            final_score=0.3,
        ),
        video_gcs_uri="gs://bucket/video.mp4",
    )

    await client.create_session(ctx)
    await client.complete_session(ctx)
    await client.fail_session(ctx, "boom")

    sessions = client._db.collection("sessions").documents  # type: ignore[attr-defined]
    assert sessions["session-1"]["mode"] == "experience"
    assert sessions["session-1"]["status"] == "failed"
    assert sessions["session-1"]["state_key"] == "unknown_happy_curious_cat"
    assert sessions["session-1"]["template_id"] == "video-1"
    assert sessions["session-1"]["video_gcs_uri"] == "gs://bucket/video.mp4"
    assert sessions["session-1"]["error"] == "boom"


async def test_get_session_returns_document(monkeypatch: MonkeyPatch) -> None:
    client = _make_client(monkeypatch)
    sessions = client._db.collection("sessions").documents  # type: ignore[attr-defined]
    sessions["session-1"] = {
        "session_id": "session-1",
        "mode": "experience",
        "status": "done",
        "template_id": "video-1",
        "state_key": "unknown_happy_curious_cat",
    }

    document = await client.get_session("session-1")

    assert document.session_id == "session-1"
    assert document.status == "done"


async def test_get_session_raises_when_missing(monkeypatch: MonkeyPatch) -> None:
    client = _make_client(monkeypatch)

    try:
        await client.get_session("missing")
    except ResourceNotFoundError as exc:
        assert exc.error_code == "NOT_FOUND"
    else:
        raise AssertionError("ResourceNotFoundError was not raised")


async def test_get_bandit_entries_and_active_templates(monkeypatch: MonkeyPatch) -> None:
    client = _make_client(monkeypatch)
    bandit_table = client._db.collection("bandit_table").documents  # type: ignore[attr-defined]
    templates = client._db.collection("templates").documents  # type: ignore[attr-defined]
    bandit_table["unknown__video-1"] = {
        "template_id": "video-1",
        "state_key": "unknown_happy_curious_cat",
        "selection_count": 2,
        "cumulative_reward": 1.0,
        "mean_reward": 0.5,
    }
    templates["video-2"] = {
        "template_id": "video-2",
        "name": "second",
        "prompt_text": "p2",
        "is_active": True,
        "auto_generated": False,
    }
    templates["video-1"] = {
        "template_id": "video-1",
        "name": "first",
        "prompt_text": "p1",
        "is_active": True,
        "auto_generated": False,
    }

    entries = await client.get_bandit_entries_by_state_key("unknown_happy_curious_cat")
    active_templates = await client.get_active_templates()

    assert list(entries) == ["video-1"]
    assert [template.template_id for template in active_templates] == ["video-1", "video-2"]


async def test_update_bandit_entry_creates_and_updates(monkeypatch: MonkeyPatch) -> None:
    client = _make_client(monkeypatch)

    await client.update_bandit_entry("video-1", "unknown_happy_curious_cat", 1.0)
    await client.update_bandit_entry("video-1", "unknown_happy_curious_cat", -0.5)

    document = client._db.collection("bandit_table").documents["unknown_happy_curious_cat__video-1"]  # type: ignore[attr-defined]
    assert document["selection_count"] == 2
    assert document["cumulative_reward"] == 0.5
    assert document["mean_reward"] == 0.25


async def test_save_feedback_persists_payload(monkeypatch: MonkeyPatch) -> None:
    client = _make_client(monkeypatch)

    await client.save_feedback("session-1", "video-1", "good", 1.0)

    feedback_documents = list(client._db.collection("feedbacks").documents.values())  # type: ignore[attr-defined]
    assert len(feedback_documents) == 1
    assert feedback_documents[0]["session_id"] == "session-1"
    assert feedback_documents[0]["template_id"] == "video-1"
    assert feedback_documents[0]["reaction"] == "good"
    assert feedback_documents[0]["reward"] == 1.0


def test_require_snapshot_dict_raises_on_none(monkeypatch: MonkeyPatch) -> None:
    client = _make_client(monkeypatch)

    try:
        client._require_snapshot_dict(None, "doc-1")
    except FirestoreError as exc:
        assert exc.error_code == "FIRESTORE_FAILED"
    else:
        raise AssertionError("FirestoreError was not raised")


async def test_create_session_wraps_google_api_errors(monkeypatch: MonkeyPatch) -> None:
    class ErrorDocumentReference(FakeDocumentReference):
        async def set(self, payload: dict[str, object]) -> None:
            del payload
            raise GoogleAPICallError("boom")

    class ErrorCollection(FakeCollection):
        def document(self, document_id: str) -> ErrorDocumentReference:
            return ErrorDocumentReference(self, document_id)

    class ErrorAsyncClient(FakeAsyncClient):
        def __init__(self, project: str | None = None, database: str | None = None) -> None:
            super().__init__(project=project, database=database)
            self.collections["sessions"] = ErrorCollection({})

    monkeypatch.setattr("src.services.firestore.client.firestore.AsyncClient", ErrorAsyncClient)
    monkeypatch.setattr(
        "src.services.firestore.client.firestore.async_transactional",
        lambda fn: fn,
    )
    monkeypatch.setattr("src.services.firestore.client.firestore.SERVER_TIMESTAMP", "SERVER_TS")
    client = FirestoreClient(settings=Settings(gcp_project_id="demo"))

    try:
        await client.create_session(
            GenerationContext(
                session_id="session-1",
                mode="experience",
                image_base64="image",
                audio_base64=None,
                user_context=None,
            ),
        )
    except FirestoreError as exc:
        assert exc.error_code == "FIRESTORE_FAILED"
    else:
        raise AssertionError("FirestoreError was not raised")
