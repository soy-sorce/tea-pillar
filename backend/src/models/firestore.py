"""Firestore document schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from src.domain.statuses import RewardStatus, SessionMode, SessionStatus


class SessionDocument(BaseModel):
    """sessions/{session_id}."""

    session_id: str
    mode: SessionMode
    status: SessionStatus
    reward_status: RewardStatus = RewardStatus.NOT_STARTED
    state_key: str | None = None
    template_id: str | None = None
    user_context: str | None = None
    video_gcs_uri: str | None = None
    reaction_video_gcs_uri: str | None = None
    reward_event_id: str | None = None
    error: str | None = None
    created_at: datetime | None = None
    generated_at: datetime | None = None
    completed_at: datetime | None = None


class BanditStateDocument(BaseModel):
    """bandit_state/{state_key}__{template_id}."""

    template_id: str
    state_key: str
    alpha: float = Field(default=1.0)
    beta: float = Field(default=1.0)
    selection_count: int = Field(default=0)
    last_reward: float | None = None
    reward_sum: float = Field(default=0.0)
    updated_at: datetime | None = None


class TemplateDocument(BaseModel):
    """templates/{template_id}."""

    template_id: str
    name: str
    prompt_text: str
    is_active: bool = True
    auto_generated: bool = False
    created_at: datetime | None = None


class RewardEventDocument(BaseModel):
    """reward_events/{reward_event_id}."""

    reward_event_id: str
    session_id: str
    template_id: str
    state_key: str
    reaction_video_gcs_uri: str
    paw_hit_count: int
    gaze_duration_seconds: float
    reward: float
    analysis_status: str = RewardStatus.DONE
    analysis_model_versions: dict[str, str] = Field(default_factory=dict)
    created_at: datetime | None = None
    analyzed_at: datetime | None = None
