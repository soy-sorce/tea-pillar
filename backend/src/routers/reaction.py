"""Routes for reaction video upload URL issuance and completion notification."""

from fastapi import APIRouter, BackgroundTasks, Depends, Response, status

from src.config import Settings, get_settings
from src.dependencies import (
    get_firestore_client,
    get_reaction_video_storage_service,
    get_reward_analysis_service,
)
from src.models.request import ReactionUploadCompleteRequest, RewardAnalysisTaskRequest
from src.models.response import ErrorResponse, ReactionUploadResponse, ReactionUploadUrlResponse
from src.repositories.firestore import FirestoreClient
from src.services.rate_limit.dependencies import (
    enforce_reaction_complete_limits,
    enforce_reaction_upload_limits,
)
from src.services.reward_analysis.service import RewardAnalysisService
from src.services.session_policy import SessionPolicy
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
    _: None = Depends(enforce_reaction_upload_limits),
    settings: Settings = Depends(get_settings),
    firestore: FirestoreClient = Depends(get_firestore_client),
    storage: ReactionVideoStorageService = Depends(get_reaction_video_storage_service),
) -> ReactionUploadUrlResponse:
    session = await firestore.get_session(session_id=session_id)
    SessionPolicy.require_generated_for_reaction_upload(session)

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
    _: None = Depends(enforce_reaction_complete_limits),
    firestore: FirestoreClient = Depends(get_firestore_client),
    storage: ReactionVideoStorageService = Depends(get_reaction_video_storage_service),
    reward_analysis: RewardAnalysisService = Depends(get_reward_analysis_service),
) -> ReactionUploadResponse:
    session = await firestore.get_session(session_id=session_id)
    SessionPolicy.require_generated_for_reaction_registration(session)
    assert session.template_id is not None
    assert session.state_key is not None

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
