"""TypedDict schemas for the custom model response."""

from typing import NotRequired, TypedDict


class EndpointFeatures(TypedDict):
    """v1 feature payload."""

    emotion_happy: float
    emotion_sad: float
    emotion_angry: float
    pose_mean_confidence: float
    pose_x_span: float
    pose_y_span: float
    pose_area_ratio: float
    pose_centroid_x: float
    pose_centroid_y: float
    pose_pc1_variance: float
    pose_pc2_variance: float
    pose_pc_ratio: float
    pose_principal_angle_sin: float
    pose_principal_angle_cos: float
    pose_compactness: float
    clip_attentive_cat: float
    clip_relaxed_cat: float
    clip_stressed_cat: float
    clip_playful_cat: float
    clip_sleepy_cat: float
    clip_curious_cat: float
    clip_alert_cat: float
    clip_comfortable_cat: float


class EndpointAuxLabels(TypedDict):
    """Auxiliary labels for backend state assembly."""

    emotion_label: str
    clip_top_label: str
    meow_label: NotRequired[str | None]


class EndpointPrediction(TypedDict):
    """Full endpoint response."""

    features: EndpointFeatures
    aux_labels: EndpointAuxLabels
    predicted_rewards: dict[str, float]
