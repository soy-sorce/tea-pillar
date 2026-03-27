"""Internal service-layer models."""

from dataclasses import dataclass, field


@dataclass(slots=True)
class CatFeatures:
    """Normalized model output from the model service."""

    features: dict[str, float]
    emotion_label: str
    clip_top_label: str
    meow_label: str | None
    predicted_rewards: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class BanditSelection:
    """Template selected by Thompson Sampling."""

    template_id: str
    template_name: str
    prompt_text: str
    predicted_reward: float
    alpha: float
    beta: float
    bandit_score: float
    final_score: float


@dataclass(slots=True)
class RewardAnalysisResult:
    """Normalized reward analysis output."""

    paw_hit_count: int
    gaze_duration_seconds: float
    reward: float
    analysis_model_versions: dict[str, str]


@dataclass(slots=True)
class GenerationContext:
    """State carried through the /generate pipeline."""

    session_id: str
    mode: str
    image_base64: str
    audio_base64: str | None
    user_context: str | None
    cat_features: CatFeatures | None = None
    state_key: str | None = None
    bandit_selection: BanditSelection | None = None
    generated_prompt: str | None = None
    video_gcs_uri: str | None = None
    video_signed_url: str | None = None
