"""Firestore document schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class SessionDocument(BaseModel):
    """sessions/{session_id}."""

    session_id: str
    mode: str
    status: str
    state_key: str | None = None
    template_id: str | None = None
    fallback_used: bool | None = None
    user_context: str | None = None
    video_gcs_uri: str | None = None
    error: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None


class BanditTableDocument(BaseModel):
    """bandit_table/{state_key}__{template_id}."""

    template_id: str
    state_key: str
    selection_count: int = Field(default=1)
    cumulative_reward: float = Field(default=0.0)
    mean_reward: float = Field(default=0.0)
    updated_at: datetime | None = None


class TemplateDocument(BaseModel):
    """templates/{template_id}."""

    template_id: str
    name: str
    prompt_text: str
    is_active: bool = True
    auto_generated: bool = False
    created_at: datetime | None = None


class FeedbackDocument(BaseModel):
    """feedbacks/{feedback_id}."""

    feedback_id: str
    session_id: str
    template_id: str
    reaction: str
    reward: float
    created_at: datetime | None = None
