"""Unit tests for session workflow policy checks."""

from src.domain.statuses import RewardStatus, SessionMode, SessionStatus
from src.exceptions import SessionConflictError
from src.models.firestore import SessionDocument
from src.services.session_policy import SessionPolicy


def _session(
    *,
    mode: SessionMode = SessionMode.PRODUCTION,
    status: SessionStatus = SessionStatus.GENERATED,
    reward_status: RewardStatus = RewardStatus.NOT_STARTED,
    template_id: str | None = "video-1",
    state_key: str | None = "unknown_happy_curious_cat",
) -> SessionDocument:
    return SessionDocument(
        session_id="session-1",
        mode=mode,
        status=status,
        reward_status=reward_status,
        template_id=template_id,
        state_key=state_key,
    )


def test_upload_policy_accepts_generated_production_session() -> None:
    SessionPolicy.require_generated_for_reaction_upload(_session())


def test_upload_policy_rejects_non_production_session() -> None:
    try:
        SessionPolicy.require_generated_for_reaction_upload(_session(mode=SessionMode.EXPERIENCE))
    except SessionConflictError as exc:
        assert exc.error_code == "SESSION_CONFLICT"
        assert exc.detail == "session_mode=experience"
    else:
        raise AssertionError("SessionConflictError was not raised")


def test_registration_policy_requires_template_and_state_key() -> None:
    try:
        SessionPolicy.require_generated_for_reaction_registration(
            _session(template_id=None, state_key=None)
        )
    except SessionConflictError as exc:
        assert exc.detail == "template_id_or_state_key_missing"
    else:
        raise AssertionError("SessionConflictError was not raised")
