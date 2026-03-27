"""Routes for reaction video upload URL issuance and completion notification."""

from fastapi import APIRouter, BackgroundTasks, Depends, Response, status
from src.config import Settings, get_settings
from src.exceptions import SessionConflictError
from src.models.request import ReactionUploadCompleteRequest, RewardAnalysisTaskRequest
from src.models.response import ErrorResponse, ReactionUploadResponse, ReactionUploadUrlResponse
from src.services.firestore.client import FirestoreClient
from src.services.reward_analysis.service import RewardAnalysisService
from src.services.storage.reaction_video import ReactionVideoStorageService

router = APIRouter(tags=["reaction"])


@router.options(
    "/sessions/{session_id}/reaction-upload-url",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def reaction_upload_url_options(session_id: str) -> Response:
    del session_id
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/sessions/{session_id}/reaction-upload-url",
    response_model=ReactionUploadUrlResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
    },
)
async def issue_reaction_upload_url(
    session_id: str,
    settings: Settings = Depends(get_settings),
) -> ReactionUploadUrlResponse:
    firestore = FirestoreClient(settings=settings)
    storage = ReactionVideoStorageService(settings=settings)

    session = await firestore.get_session(session_id=session_id)
    if session.status != "generated":
        raise SessionConflictError(
            message="生成済みセッションに対してのみ upload URL を発行できます",
            detail=f"session_status={session.status}",
        )

    upload_url, reaction_video_gcs_uri = storage.issue_upload_url(session_id=session_id)
    return ReactionUploadUrlResponse(
        session_id=session_id,
        upload_url=upload_url,
        reaction_video_gcs_uri=reaction_video_gcs_uri,
        expires_in_seconds=settings.reaction_video_upload_url_expires_seconds,
    )


@router.options("/sessions/{session_id}/reaction", status_code=status.HTTP_204_NO_CONTENT)
async def reaction_options(session_id: str) -> Response:
    del session_id
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/sessions/{session_id}/reaction",
    response_model=ReactionUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
        504: {"model": ErrorResponse},
    },
)
async def register_reaction_video(
    session_id: str,
    request: ReactionUploadCompleteRequest,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings),
) -> ReactionUploadResponse:
    firestore = FirestoreClient(settings=settings)
    storage = ReactionVideoStorageService(settings=settings)
    reward_analysis = RewardAnalysisService(settings=settings)

    session = await firestore.get_session(session_id=session_id)
    if session.status != "generated":
        raise SessionConflictError(
            message="生成済みセッションに対してのみ反応動画を登録できます",
            detail=f"session_status={session.status}",
        )
    if not session.template_id or not session.state_key:
        raise SessionConflictError(
            message="反応動画受付に必要なセッション情報が不足しています",
            detail="template_id_or_state_key_missing",
        )

    reaction_video_gcs_uri = storage.validate_gcs_uri(
        session_id=session_id,
        reaction_video_gcs_uri=request.reaction_video_gcs_uri,
    )
    await firestore.attach_reaction_video(
        session_id=session_id,
        reaction_video_gcs_uri=reaction_video_gcs_uri,
    )
    background_tasks.add_task(
        reward_analysis.analyze,
        RewardAnalysisTaskRequest(
            session_id=session_id,
            reaction_video_gcs_uri=reaction_video_gcs_uri,
            template_id=session.template_id,
            state_key=session.state_key,
        ),
    )

    return ReactionUploadResponse(
        session_id=session_id,
        reaction_video_gcs_uri=reaction_video_gcs_uri,
    )
