# backend/src/models/internal.py
"""サービス層で使用する内部データクラス定義."""
from dataclasses import dataclass, field


@dataclass
class CatFeatures:
    """猫モデル Endpoint の出力を格納する内部データクラス."""

    # 顔感情スコア
    emotion_label: str                    # "happy" | "sad" | "angry"
    emotion_probs: dict[str, float]       # {"happy": 0.72, "sad": 0.15, "angry": 0.13}

    # 鳴き声分類
    meow_label: str | None                # "brushing" | "waiting_for_food" | "isolation" | None
    meow_probs: dict[str, float] | None

    # ポーズ特徴量（12次元の角度特徴）
    pose_angles: list[float]              # 12次元
    pose_activity_score: float

    # CLIP ゼロショットスコア（8種）
    clip_scores: dict[str, float]         # {"attentive": 0.81, "relaxed": 0.34, ...}

    # LightGBM Ranker スコア（11テンプレート）
    ranker_scores: list[float]            # shape: (11,)


@dataclass
class BanditSelection:
    """Bandit による選択結果."""

    template_id: str
    template_name: str
    prompt_text: str
    final_score: float
    ranker_score: float
    ucb_bonus: float


@dataclass
class GenerationContext:
    """/generate 処理全体で引き回すコンテキスト."""

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