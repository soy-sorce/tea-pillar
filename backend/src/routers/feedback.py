"""POST /feedback route."""

import structlog
from fastapi import APIRouter, Depends

from src.config import Settings, get_settings
from src.exceptions import SessionConflictError
from src.models.request import FeedbackRequest
from src.models.response import ErrorResponse, FeedbackResponse
from src.services.bandit.ucb import UCBBandit
from src.services.firestore.client import FirestoreClient

logger = structlog.get_logger(__name__)
router = APIRouter(tags=["feedback"])

REACTION_TO_REWARD: dict[str, float] = {
    "good": 1.0,
    "neutral": 0.0,
    "bad": -0.5,
}


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    responses={
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Record human feedback and update the bandit table",
)
async def feedback(
    request: FeedbackRequest,
    settings: Settings = Depends(get_settings),
) -> FeedbackResponse:
    """Persist feedback and update UCB statistics."""
    reward = REACTION_TO_REWARD[request.reaction]
    firestore = FirestoreClient(settings=settings)
    bandit = UCBBandit(settings=settings, firestore_client=firestore)

    session = await firestore.get_session(session_id=request.session_id)
    # TODO(shouh): Reconsider whether strict 409 validation is best for demo flow.
    if session.status != "done":
        raise SessionConflictError(
            message="完了済みセッションに対してのみフィードバックを送信できます",
            detail=f"session_status={session.status}",
        )
    if not session.template_id or not session.state_key:
        raise SessionConflictError(
            message="フィードバック対象のセッション情報が不足しています",
            detail="template_id_or_state_key_missing",
        )

    logger.info(
        "feedback_received",
        session_id=request.session_id,
        reaction=request.reaction,
        reward=reward,
        template_id=session.template_id,
    )

    await firestore.save_feedback(
        session_id=request.session_id,
        template_id=session.template_id,
        reaction=request.reaction,
        reward=reward,
    )
    await bandit.update(
        template_id=session.template_id,
        state_key=session.state_key,
        reward=reward,
    )

    return FeedbackResponse(
        reward=reward,
        updated_template_id=session.template_id,
    )
