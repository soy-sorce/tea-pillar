"""Reward analysis entrypoint for the model service."""

from __future__ import annotations

from typing import Self

from .artifacts import load_artifacts
from .reward.gaze_estimator import GazeEstimator
from .reward.paw_detector import PawDetector
from .reward.video_io import VideoClip
from .schemas import RewardAnalysisRequest, RewardAnalysisResponse


class RewardAnalyzer:
    """Analyze a reaction video and return reward metrics."""

    def __init__(self: Self) -> None:
        self._artifacts = load_artifacts()
        self._paw_detector = PawDetector()
        self._gaze_estimator = GazeEstimator()

    @property
    def implementation_name(self: Self) -> str:
        """Return the analyzer implementation marker."""
        return "yolov8-mediapipe-v1"

    def analyze(self: Self, request: RewardAnalysisRequest) -> RewardAnalysisResponse:
        """Analyze a reaction video from GCS."""
        clip = VideoClip.from_gcs_uri(request.reaction_video_gcs_uri)
        paw_metrics = self._paw_detector.detect(clip.local_path)
        gaze_metrics = self._gaze_estimator.estimate(clip.local_path)
        reward = round(
            (self._paw_alpha * paw_metrics.paw_hit_count)
            + (self._gaze_beta * gaze_metrics.gaze_duration_seconds),
            6,
        )
        return RewardAnalysisResponse(
            paw_hit_count=paw_metrics.paw_hit_count,
            gaze_duration_seconds=gaze_metrics.gaze_duration_seconds,
            reward=reward,
            analysis_model_versions={
                "paw_detector": self.implementation_name,
                "gaze_estimator": self.implementation_name,
            },
        )

    @property
    def _paw_alpha(self: Self) -> float:
        if self._artifacts is None:
            return 0.3
        return float(self._artifacts.reward_formula.get("paw_alpha", 0.3))

    @property
    def _gaze_beta(self: Self) -> float:
        if self._artifacts is None:
            return 0.05
        return float(self._artifacts.reward_formula.get("gaze_beta", 0.05))
