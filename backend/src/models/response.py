"""Response schemas."""

from typing import Literal

from pydantic import BaseModel, Field


class GenerateResponse(BaseModel):
    """POST /generate response."""

    session_id: str = Field(...)
    video_url: str = Field(...)
    state_key: str = Field(...)
    template_id: str = Field(...)
    template_name: str = Field(...)


class ReactionUploadResponse(BaseModel):
    """POST /sessions/{session_id}/reaction response."""

    session_id: str = Field(...)
    status: Literal["accepted"] = "accepted"
    reaction_video_gcs_uri: str = Field(...)


class ReactionUploadUrlResponse(BaseModel):
    """POST /sessions/{session_id}/reaction-upload-url response."""

    session_id: str = Field(...)
    upload_url: str = Field(...)
    reaction_video_gcs_uri: str = Field(...)
    expires_in_seconds: int = Field(...)


class HealthResponse(BaseModel):
    """GET /health response."""

    status: Literal["ok"] = "ok"
    environment: str = Field(...)


class RootResponse(BaseModel):
    """GET / response."""

    service: str = Field(...)
    status: Literal["ok"] = "ok"
    environment: str = Field(...)


class ErrorResponse(BaseModel):
    """Error response body."""

    error_code: str = Field(...)
    message: str = Field(...)
