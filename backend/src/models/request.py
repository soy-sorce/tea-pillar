"""Request schemas."""

from typing import Literal

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    """POST /generate request."""

    mode: Literal["experience", "production"] = Field(...)
    image_base64: str = Field(..., min_length=1)
    audio_base64: str | None = Field(default=None)
    user_context: str | None = Field(default=None, max_length=500)


class FeedbackRequest(BaseModel):
    """POST /feedback request."""

    session_id: str = Field(..., min_length=1)
    reaction: Literal["good", "neutral", "bad"] = Field(...)
