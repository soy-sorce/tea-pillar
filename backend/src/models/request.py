"""Request schemas."""

from typing import Literal

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    """POST /generate request."""

    mode: Literal["experience", "production"] = Field(...)
    image_base64: str = Field(..., min_length=1)
    audio_base64: str | None = Field(default=None)
    user_context: str | None = Field(default=None, max_length=500)


class RewardAnalysisTaskRequest(BaseModel):
    """Task payload for internal reward analysis."""

    session_id: str = Field(..., min_length=1)
    reaction_video_gcs_uri: str = Field(..., min_length=1)
    template_id: str = Field(..., min_length=1)
    state_key: str = Field(..., min_length=1)


class ReactionUploadCompleteRequest(BaseModel):
    """POST /sessions/{session_id}/reaction request."""

    reaction_video_gcs_uri: str = Field(..., min_length=1)
