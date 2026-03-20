"""Firestore client wrapper."""

import uuid
from collections.abc import Mapping
from typing import Any, Self, cast

from google.api_core.exceptions import DeadlineExceeded, GoogleAPICallError, RetryError
from google.cloud import firestore
from google.cloud.firestore import AsyncClient

from src.config import Settings
from src.exceptions import FirestoreError, ResourceNotFoundError
from src.models.firestore import BanditTableDocument, SessionDocument, TemplateDocument
from src.models.internal import GenerationContext

_COL_SESSIONS = "sessions"
_COL_BANDIT_TABLE = "bandit_table"
_COL_TEMPLATES = "templates"
_COL_FEEDBACKS = "feedbacks"


class FirestoreClient:
    """Centralized Firestore data access."""

    def __init__(self: Self, settings: Settings) -> None:
        self._db: AsyncClient = firestore.AsyncClient(
            project=settings.gcp_project_id or None,
            database=settings.firestore_database_id,
        )

    async def create_session(self: Self, ctx: GenerationContext) -> None:
        """Insert a generating session document."""
        document = {
            "session_id": ctx.session_id,
            "mode": ctx.mode,
            "status": "generating",
            "user_context": ctx.user_context,
            "created_at": firestore.SERVER_TIMESTAMP,
        }
        try:
            await self._db.collection(_COL_SESSIONS).document(ctx.session_id).set(document)
        except (DeadlineExceeded, GoogleAPICallError, RetryError) as exc:
            raise FirestoreError(
                message="セッションの作成に失敗しました",
                detail=str(exc),
            ) from exc

    async def complete_session(self: Self, ctx: GenerationContext) -> None:
        """Update a session to done."""
        update = {
            "status": "done",
            "state_key": ctx.state_key,
            "template_id": ctx.bandit_selection.template_id if ctx.bandit_selection else None,
            "video_gcs_uri": ctx.video_gcs_uri,
            "completed_at": firestore.SERVER_TIMESTAMP,
        }
        try:
            await self._db.collection(_COL_SESSIONS).document(ctx.session_id).update(update)
        except (DeadlineExceeded, GoogleAPICallError, RetryError) as exc:
            raise FirestoreError(
                message="セッションの完了更新に失敗しました",
                detail=str(exc),
            ) from exc

    async def fail_session(self: Self, ctx: GenerationContext, error_msg: str) -> None:
        """Update a session to failed."""
        update = {
            "status": "failed",
            "error": error_msg,
            "completed_at": firestore.SERVER_TIMESTAMP,
        }
        try:
            await self._db.collection(_COL_SESSIONS).document(ctx.session_id).update(update)
        except (DeadlineExceeded, GoogleAPICallError, RetryError) as exc:
            raise FirestoreError(
                message="失敗セッションの保存に失敗しました",
                detail=str(exc),
            ) from exc

    async def get_session(self: Self, session_id: str) -> SessionDocument:
        """Fetch a session by ID."""
        try:
            snapshot = await self._db.collection(_COL_SESSIONS).document(session_id).get()
        except (DeadlineExceeded, GoogleAPICallError, RetryError) as exc:
            raise FirestoreError(
                message="セッションの取得に失敗しました",
                detail=str(exc),
            ) from exc

        if not snapshot.exists:
            raise ResourceNotFoundError(
                message="セッションが見つかりません",
                detail=f"session_id={session_id}",
            )
        return SessionDocument(**self._require_snapshot_dict(snapshot.to_dict(), session_id))

    async def get_bandit_entries_by_state_key(
        self: Self,
        state_key: str,
    ) -> dict[str, BanditTableDocument]:
        """Fetch all bandit entries for a state key."""
        try:
            stream = (
                self._db.collection(_COL_BANDIT_TABLE).where("state_key", "==", state_key).stream()
            )
            entries: dict[str, BanditTableDocument] = {}
            async for snapshot in stream:
                entry = BanditTableDocument(**self._require_snapshot_dict(snapshot.to_dict()))
                entries[entry.template_id] = entry
            return entries
        except (DeadlineExceeded, GoogleAPICallError, RetryError) as exc:
            raise FirestoreError(
                message="Bandit テーブルの取得に失敗しました",
                detail=str(exc),
            ) from exc

    async def update_bandit_entry(
        self: Self,
        template_id: str,
        state_key: str,
        reward: float,
    ) -> None:
        """Transactionally update the bandit statistics."""
        document_id = f"{state_key}__{template_id}"
        document_ref = self._db.collection(_COL_BANDIT_TABLE).document(document_id)

        @firestore.async_transactional
        async def update_in_transaction(
            transaction: firestore.AsyncTransaction,
        ) -> None:
            snapshot = await document_ref.get(transaction=transaction)
            if snapshot.exists:
                data = self._require_snapshot_dict(snapshot.to_dict(), document_id)
                selection_count = int(data["selection_count"]) + 1
                cumulative_reward = float(data["cumulative_reward"]) + reward
            else:
                selection_count = 1
                cumulative_reward = reward

            transaction.set(
                document_ref,
                {
                    "template_id": template_id,
                    "state_key": state_key,
                    "selection_count": selection_count,
                    "cumulative_reward": cumulative_reward,
                    "mean_reward": cumulative_reward / selection_count,
                    "updated_at": firestore.SERVER_TIMESTAMP,
                },
            )

        try:
            transaction = self._db.transaction()
            await update_in_transaction(transaction)
        except (DeadlineExceeded, GoogleAPICallError, RetryError) as exc:
            raise FirestoreError(
                message="Bandit テーブルの更新に失敗しました",
                detail=str(exc),
            ) from exc

    async def get_active_templates(self: Self) -> list[TemplateDocument]:
        """Return active templates ordered by template_id."""
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

    async def save_feedback(
        self: Self,
        session_id: str,
        template_id: str,
        reaction: str,
        reward: float,
    ) -> None:
        """Persist a feedback event."""
        feedback_id = str(uuid.uuid4())
        document = {
            "feedback_id": feedback_id,
            "session_id": session_id,
            "template_id": template_id,
            "reaction": reaction,
            "reward": reward,
            "created_at": firestore.SERVER_TIMESTAMP,
        }
        try:
            await self._db.collection(_COL_FEEDBACKS).document(feedback_id).set(document)
        except (DeadlineExceeded, GoogleAPICallError, RetryError) as exc:
            raise FirestoreError(
                message="フィードバックの保存に失敗しました",
                detail=str(exc),
            ) from exc

    def _require_snapshot_dict(
        self: Self,
        data: dict[str, Any] | None,
        document_hint: str = "unknown",
    ) -> Mapping[str, Any]:
        """Normalize Firestore snapshot payloads to a mapping."""
        if data is None:
            raise FirestoreError(
                message="Firestore ドキュメントの内容が不正です",
                detail=f"document={document_hint}",
            )
        return cast(Mapping[str, Any], data)
