"""Firestore client wrapper."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Any, Self, cast

from google.api_core.exceptions import DeadlineExceeded, GoogleAPICallError, RetryError
from google.cloud import firestore
from google.cloud.firestore import AsyncClient

from src.config import Settings
from src.domain.statuses import RewardStatus, SessionStatus
from src.exceptions import FirestoreError, ResourceNotFoundError
from src.models.firestore import (
    BanditStateDocument,
    RewardEventDocument,
    SessionDocument,
    TemplateDocument,
)
from src.models.internal import GenerationContext, RewardAnalysisResult

_COL_SESSIONS = "sessions"
_COL_BANDIT_STATE = "bandit_state"
_COL_TEMPLATES = "templates"
_COL_REWARD_EVENTS = "reward_events"


class FirestoreClient:
    """Centralized Firestore data access."""

    def __init__(self: Self, settings: Settings) -> None:
        self._settings = settings
        self._db: AsyncClient = firestore.AsyncClient(
            project=settings.gcp_project_id or None,
            database=settings.firestore_database_id,
        )

    async def create_session(self: Self, ctx: GenerationContext) -> None:
        document = {
            "session_id": ctx.session_id,
            "mode": ctx.mode,
            "status": SessionStatus.GENERATING,
            "reward_status": RewardStatus.NOT_STARTED,
            "user_context": ctx.user_context,
            "created_at": firestore.SERVER_TIMESTAMP,
        }
        await self._set_document(
            _COL_SESSIONS,
            ctx.session_id,
            document,
            "セッションの作成に失敗しました",
        )

    async def mark_session_generated(self: Self, ctx: GenerationContext) -> None:
        update = {
            "status": SessionStatus.GENERATED,
            "reward_status": RewardStatus.NOT_STARTED,
            "state_key": ctx.state_key,
            "template_id": ctx.bandit_selection.template_id if ctx.bandit_selection else None,
            "video_gcs_uri": ctx.video_gcs_uri,
            "generated_at": firestore.SERVER_TIMESTAMP,
        }
        await self._update_document(
            _COL_SESSIONS,
            ctx.session_id,
            update,
            "セッションの生成完了更新に失敗しました",
        )

    async def fail_session(self: Self, ctx: GenerationContext, error_msg: str) -> None:
        update = {
            "status": SessionStatus.FAILED,
            "error": error_msg,
            "completed_at": firestore.SERVER_TIMESTAMP,
        }
        await self._update_document(
            _COL_SESSIONS,
            ctx.session_id,
            update,
            "失敗セッションの保存に失敗しました",
        )

    async def get_session(self: Self, session_id: str) -> SessionDocument:
        try:
            snapshot = await self._db.collection(_COL_SESSIONS).document(session_id).get()
        except (DeadlineExceeded, GoogleAPICallError, RetryError) as exc:
            raise FirestoreError(message="セッションの取得に失敗しました", detail=str(exc)) from exc

        if not snapshot.exists:
            raise ResourceNotFoundError(
                message="セッションが見つかりません",
                detail=f"session_id={session_id}",
            )
        return SessionDocument(**self._require_snapshot_dict(snapshot.to_dict(), session_id))

    async def attach_reaction_video(
        self: Self,
        session_id: str,
        reaction_video_gcs_uri: str,
    ) -> None:
        update = {
            "reaction_video_gcs_uri": reaction_video_gcs_uri,
            "reward_status": RewardStatus.PENDING,
        }
        await self._update_document(
            _COL_SESSIONS,
            session_id,
            update,
            "反応動画 URI の保存に失敗しました",
        )

    async def create_reward_event(
        self: Self,
        *,
        session_id: str,
        template_id: str,
        state_key: str,
        reaction_video_gcs_uri: str,
        result: RewardAnalysisResult,
    ) -> str:
        reward_event_id = str(uuid.uuid4())
        document = RewardEventDocument(
            reward_event_id=reward_event_id,
            session_id=session_id,
            template_id=template_id,
            state_key=state_key,
            reaction_video_gcs_uri=reaction_video_gcs_uri,
            paw_hit_count=result.paw_hit_count,
            gaze_duration_seconds=result.gaze_duration_seconds,
            reward=result.reward,
            analysis_model_versions=result.analysis_model_versions,
        ).model_dump()
        document["created_at"] = firestore.SERVER_TIMESTAMP
        document["analyzed_at"] = firestore.SERVER_TIMESTAMP
        await self._set_document(
            _COL_REWARD_EVENTS,
            reward_event_id,
            document,
            "報酬イベントの保存に失敗しました",
        )
        return reward_event_id

    async def mark_session_completed(
        self: Self,
        *,
        session_id: str,
        reward_event_id: str,
    ) -> None:
        update = {
            "status": SessionStatus.COMPLETED,
            "reward_status": RewardStatus.DONE,
            "reward_event_id": reward_event_id,
            "completed_at": firestore.SERVER_TIMESTAMP,
        }
        await self._update_document(
            _COL_SESSIONS,
            session_id,
            update,
            "セッション完了更新に失敗しました",
        )

    async def mark_session_reward_failed(self: Self, *, session_id: str, error_msg: str) -> None:
        update = {
            "reward_status": RewardStatus.FAILED,
            "error": error_msg,
        }
        await self._update_document(
            _COL_SESSIONS,
            session_id,
            update,
            "報酬失敗状態の保存に失敗しました",
        )

    async def get_bandit_states_by_state_key(
        self: Self,
        state_key: str,
    ) -> dict[str, BanditStateDocument]:
        try:
            stream = (
                self._db.collection(_COL_BANDIT_STATE).where("state_key", "==", state_key).stream()
            )
            entries: dict[str, BanditStateDocument] = {}
            async for snapshot in stream:
                entry = BanditStateDocument(**self._require_snapshot_dict(snapshot.to_dict()))
                entries[entry.template_id] = entry
            return entries
        except (DeadlineExceeded, GoogleAPICallError, RetryError) as exc:
            raise FirestoreError(
                message="Bandit 状態の取得に失敗しました",
                detail=str(exc),
            ) from exc

    async def update_bandit_state(
        self: Self,
        *,
        template_id: str,
        state_key: str,
        reward: float,
    ) -> None:
        document_id = f"{state_key}__{template_id}"
        document_ref = self._db.collection(_COL_BANDIT_STATE).document(document_id)

        @firestore.async_transactional
        async def update_in_transaction(transaction: firestore.AsyncTransaction) -> None:
            snapshot = await document_ref.get(transaction=transaction)
            if snapshot.exists:
                data = self._require_snapshot_dict(snapshot.to_dict(), document_id)
                alpha = float(data["alpha"])
                beta = float(data["beta"])
                selection_count = int(data["selection_count"])
                reward_sum = float(data["reward_sum"])
            else:
                alpha = self._settings.thompson_default_alpha
                beta = self._settings.thompson_default_beta
                selection_count = 0
                reward_sum = 0.0

            is_success = reward >= self._settings.reward_success_threshold
            if is_success:
                alpha += 1.0
            else:
                beta += 1.0
            selection_count += 1
            reward_sum += reward

            transaction.set(
                document_ref,
                {
                    "template_id": template_id,
                    "state_key": state_key,
                    "alpha": alpha,
                    "beta": beta,
                    "selection_count": selection_count,
                    "last_reward": reward,
                    "reward_sum": reward_sum,
                    "updated_at": firestore.SERVER_TIMESTAMP,
                },
            )

        try:
            transaction = self._db.transaction()
            await update_in_transaction(transaction)
        except (DeadlineExceeded, GoogleAPICallError, RetryError) as exc:
            raise FirestoreError(
                message="Bandit 状態の更新に失敗しました",
                detail=str(exc),
            ) from exc

    async def get_active_templates(self: Self) -> list[TemplateDocument]:
        try:
            stream = self._db.collection(_COL_TEMPLATES).where("is_active", "==", True).stream()
            templates = [
                TemplateDocument(**self._require_snapshot_dict(snapshot.to_dict()))
                async for snapshot in stream
            ]
        except (DeadlineExceeded, GoogleAPICallError, RetryError) as exc:
            raise FirestoreError(
                message="テンプレート一覧の取得に失敗しました",
                detail=str(exc),
            ) from exc
        return sorted(templates, key=lambda template: template.template_id)

    async def _set_document(
        self: Self,
        collection: str,
        document_id: str,
        document: Mapping[str, Any],
        message: str,
    ) -> None:
        try:
            await self._db.collection(collection).document(document_id).set(dict(document))
        except (DeadlineExceeded, GoogleAPICallError, RetryError) as exc:
            raise FirestoreError(message=message, detail=str(exc)) from exc

    async def _update_document(
        self: Self,
        collection: str,
        document_id: str,
        update: Mapping[str, Any],
        message: str,
    ) -> None:
        try:
            await self._db.collection(collection).document(document_id).update(dict(update))
        except (DeadlineExceeded, GoogleAPICallError, RetryError) as exc:
            raise FirestoreError(message=message, detail=str(exc)) from exc

    def _require_snapshot_dict(
        self: Self,
        data: dict[str, Any] | None,
        document_hint: str = "unknown",
    ) -> Mapping[str, Any]:
        if data is None:
            raise FirestoreError(
                message="Firestore ドキュメントの内容が不正です",
                detail=f"document={document_hint}",
            )
        return cast(Mapping[str, Any], data)
