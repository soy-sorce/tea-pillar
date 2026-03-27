"""Unit tests for reward analysis error handling."""

from __future__ import annotations

from typing import Any, Self, cast

from src.config import Settings
from src.exceptions import FirestoreError, RewardAnalysisError
from src.models.internal import RewardAnalysisResult
from src.models.request import RewardAnalysisTaskRequest
from src.services.reward_analysis.service import RewardAnalysisService


class FakeCatModelClient:
    def __init__(self, *, exc: Exception | None = None) -> None:
        self._exc = exc

    async def analyze_reward(
        self: Self,
        reaction_video_gcs_uri: str,
        *,
        session_id: str,
        template_id: str,
        state_key: str,
    ) -> RewardAnalysisResult:
        del reaction_video_gcs_uri, session_id, template_id, state_key
        if self._exc is not None:
            raise self._exc
        return RewardAnalysisResult(
            paw_hit_count=1,
            gaze_duration_seconds=2.0,
            reward=1.2,
            analysis_model_versions={"analyzer": "v1"},
        )


class FakeBandit:
    def __init__(self, *, exc: Exception | None = None) -> None:
        self._exc = exc

    async def update(self: Self, template_id: str, state_key: str, reward: float) -> None:
        del template_id, state_key, reward
        if self._exc is not None:
            raise self._exc


class FakeFirestoreClient:
    def __init__(
        self: Self,
        *,
        create_reward_event_exc: Exception | None = None,
        mark_completed_exc: Exception | None = None,
        mark_failed_exc: Exception | None = None,
    ) -> None:
        self._create_reward_event_exc = create_reward_event_exc
        self._mark_completed_exc = mark_completed_exc
        self._mark_failed_exc = mark_failed_exc
        self.mark_failed_calls = 0

    async def create_reward_event(self: Self, **kwargs: object) -> str:
        del kwargs
        if self._create_reward_event_exc is not None:
            raise self._create_reward_event_exc
        return "reward-event-1"

    async def mark_session_completed(self: Self, *, session_id: str, reward_event_id: str) -> None:
        del session_id, reward_event_id
        if self._mark_completed_exc is not None:
            raise self._mark_completed_exc

    async def mark_session_reward_failed(self: Self, *, session_id: str, error_msg: str) -> None:
        del session_id, error_msg
        self.mark_failed_calls += 1
        if self._mark_failed_exc is not None:
            raise self._mark_failed_exc


def _payload() -> RewardAnalysisTaskRequest:
    return RewardAnalysisTaskRequest(
        session_id="session-1",
        reaction_video_gcs_uri="gs://bucket/reaction_videos/session-1/video.mp4",
        template_id="video-1",
        state_key="unknown_happy_curious_cat",
    )


async def test_firestore_error_still_marks_session_reward_failed() -> None:
    firestore = FakeFirestoreClient(
        mark_completed_exc=FirestoreError(detail="complete failed"),
    )
    service = RewardAnalysisService(
        settings=Settings(),
        firestore_client=cast(Any, firestore),
        cat_model_client=cast(Any, FakeCatModelClient()),
        bandit=cast(Any, FakeBandit()),
    )

    try:
        await service.analyze(_payload())
    except FirestoreError as exc:
        assert exc.detail == "complete failed"
    else:
        raise AssertionError("FirestoreError was not raised")

    assert firestore.mark_failed_calls == 1


async def test_non_firestore_error_maps_to_reward_analysis_error() -> None:
    firestore = FakeFirestoreClient()
    service = RewardAnalysisService(
        settings=Settings(),
        firestore_client=cast(Any, firestore),
        cat_model_client=cast(Any, FakeCatModelClient(exc=RuntimeError("boom"))),
        bandit=cast(Any, FakeBandit()),
    )

    try:
        await service.analyze(_payload())
    except RewardAnalysisError as exc:
        assert "boom" in str(exc.detail)
    else:
        raise AssertionError("RewardAnalysisError was not raised")

    assert firestore.mark_failed_calls == 1
