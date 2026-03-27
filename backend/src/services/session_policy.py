"""Shared session-policy checks."""

from src.domain.statuses import SessionMode, SessionStatus
from src.exceptions import SessionConflictError
from src.models.firestore import SessionDocument


class SessionPolicy:
    """Validate whether a session can proceed through a workflow step."""

    @staticmethod
    def require_generated_for_reaction_upload(session: SessionDocument) -> None:
        """Allow upload URL issuance only for generated production sessions."""
        _require_generated_production_session(session)

    @staticmethod
    def require_generated_for_reaction_registration(session: SessionDocument) -> None:
        """Allow reaction registration only when required fields are ready."""
        _require_generated_production_session(session)
        if not session.template_id or not session.state_key:
            raise SessionConflictError(
                message="反応動画受付に必要なセッション情報が不足しています",
                detail="template_id_or_state_key_missing",
            )


def _require_generated_production_session(session: SessionDocument) -> None:
    if session.status != SessionStatus.GENERATED:
        raise SessionConflictError(
            message="生成済みセッションに対してのみ実行できます",
            detail=f"session_status={session.status}",
        )
    if session.mode != SessionMode.PRODUCTION:
        raise SessionConflictError(
            message="本番モードのセッションに対してのみ実行できます",
            detail=f"session_mode={session.mode}",
        )
