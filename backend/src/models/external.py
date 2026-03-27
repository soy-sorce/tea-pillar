"""Schemas for external service contracts."""

from pydantic import BaseModel, Field


class ModelAuxLabels(BaseModel):
    """Auxiliary labels returned by the model service."""

    emotion_label: str = Field(..., min_length=1)
    clip_top_label: str = Field(..., min_length=1)
    meow_label: str | None = None


class ModelPredictResponse(BaseModel):
    """Normalized `/predict` response contract."""

    features: dict[str, float]
    aux_labels: ModelAuxLabels
    predicted_rewards: dict[str, float] = Field(default_factory=dict)


class ModelRewardAnalysisResponse(BaseModel):
    """Normalized `/analyze-reward` response contract."""

    paw_hit_count: int
    gaze_duration_seconds: float
    reward: float
    analysis_model_versions: dict[str, str] = Field(default_factory=dict)
