"""Reward analysis orchestration service."""

from __future__ import annotations

from typing import Self

from src.clients.model_service import CatModelClient
from src.config import Settings
from src.exceptions import FirestoreError, RewardAnalysisError
from src.models.request import RewardAnalysisTaskRequest
from src.repositories.firestore import FirestoreClient
from src.services.bandit.thompson import ThompsonBandit


class RewardAnalysisService:
    """Execute the internal reward-analysis flow."""

    def __init__(
        self: Self,
        settings: Settings,
        *,
        firestore_client: FirestoreClient | None = None,
        cat_model_client: CatModelClient | None = None,
        bandit: ThompsonBandit | None = None,
    ) -> None:
        self._firestore = firestore_client or FirestoreClient(settings=settings)
        self._cat_model = cat_model_client or CatModelClient(settings=settings)
        self._bandit = bandit or ThompsonBandit(settings=settings, firestore_client=self._firestore)

    async def analyze(self: Self, payload: RewardAnalysisTaskRequest) -> None:
        try:
            result = await self._cat_model.analyze_reward(
                payload.reaction_video_gcs_uri,
                session_id=payload.session_id,
                template_id=payload.template_id,
                state_key=payload.state_key,
            )
            reward_event_id = await self._firestore.create_reward_event(
                session_id=payload.session_id,
                template_id=payload.template_id,
                state_key=payload.state_key,
                reaction_video_gcs_uri=payload.reaction_video_gcs_uri,
                result=result,
            )
            await self._bandit.update(
                template_id=payload.template_id,
                state_key=payload.state_key,
                reward=result.reward,
            )
            await self._firestore.mark_session_completed(
                session_id=payload.session_id,
                reward_event_id=reward_event_id,
            )
        except Exception as exc:
            try:
                await self._firestore.mark_session_reward_failed(
                    session_id=payload.session_id,
                    error_msg=str(exc),
                )
            except FirestoreError:
                pass
            if isinstance(exc, FirestoreError):
                raise
            raise RewardAnalysisError(detail=str(exc)) from exc
