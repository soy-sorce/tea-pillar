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


class FeedbackResponse(BaseModel):
    """POST /feedback response."""

    reward: float = Field(...)
    updated_template_id: str = Field(...)


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
