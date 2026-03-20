"""Request and response schemas for the model endpoint."""

from dataclasses import asdict, dataclass
from typing import Self


@dataclass(slots=True)
class PredictionRequest:
    """Normalized endpoint input."""

    image_base64: str
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
