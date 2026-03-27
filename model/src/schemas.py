"""Request and response schemas for the model service."""

from dataclasses import asdict, dataclass
from typing import Self


@dataclass(slots=True)
class PredictionRequest:
    """Normalized endpoint input."""

    image_base64: str | None
    image_gcs_uri: str | None
    audio_base64: str | None
    candidate_video_ids: list[str]


@dataclass(slots=True)
class PredictionResponse:
    """Endpoint output contract."""

    features: dict[str, float]
    aux_labels: dict[str, str | None]
    predicted_rewards: dict[str, float]

    def to_dict(self: Self) -> dict[str, object]:
        """Convert to a JSON-serializable dict."""
        return asdict(self)


@dataclass(slots=True)
class RewardAnalysisRequest:
    """Normalized reward analysis input."""

    reaction_video_gcs_uri: str
    session_id: str | None = None
    template_id: str | None = None
    state_key: str | None = None


@dataclass(slots=True)
class RewardAnalysisResponse:
    """Reward analysis output contract."""

    paw_hit_count: int
    gaze_duration_seconds: float
    reward: float
    analysis_model_versions: dict[str, str]

    def to_dict(self: Self) -> dict[str, object]:
        """Convert to a JSON-serializable dict."""
        return asdict(self)
