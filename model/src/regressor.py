"""Reward prediction."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Protocol, Self, cast

import pandas as pd  # type: ignore[import-untyped]

from src.artifacts import ArtifactBundle


class RegressorLike(Protocol):
    """Protocol for regressors with a scikit-learn-like interface."""

    def predict(self: RegressorLike, values: Sequence[Sequence[float]]) -> Sequence[float]:
        """Return predictions for rows."""


class RewardRegressor:
    """Predict rewards per candidate video."""

    def __init__(self: Self, artifacts: ArtifactBundle | None) -> None:
        self._artifacts = artifacts

    def predict(
        self: Self,
        features: dict[str, float],
        candidate_video_ids: list[str],
    ) -> dict[str, float]:
        """Predict rewards using artifacts when present, else fallback heuristics."""
        if self._artifacts is None:
            return self._fallback_predict(
                features=features, candidate_video_ids=candidate_video_ids
            )

        regressor = cast(RegressorLike, self._artifacts.regressor)
        rows = pd.DataFrame(
            [
                self._build_feature_row(
                    features=features,
                    candidate_video_id=candidate_video_id,
                    feature_columns=self._artifacts.feature_columns,
                )
                for candidate_video_id in candidate_video_ids
            ],
            columns=self._artifacts.feature_columns,
        )
        predictions = regressor.predict(rows)
        return {
            candidate_video_id: float(prediction)
            for candidate_video_id, prediction in zip(candidate_video_ids, predictions, strict=True)
        }

    def _build_feature_row(
        self: Self,
        features: dict[str, float],
        candidate_video_id: str,
        feature_columns: list[str],
    ) -> list[float]:
        """Construct a row matching training-time feature order."""
        values_by_name: dict[str, float] = {}
        for key, value in features.items():
            values_by_name[f"before_{key}"] = value
        for video_id in self._artifacts.video_id_mapping if self._artifacts else []:
            values_by_name[f"video_{video_id}"] = 1.0 if video_id == candidate_video_id else 0.0
        return [values_by_name.get(column, 0.0) for column in feature_columns]

    def _fallback_predict(
        self: Self,
        features: dict[str, float],
        candidate_video_ids: list[str],
    ) -> dict[str, float]:
        """Deterministic heuristic used until real artifacts are available."""
        base_score = (
            1.0 * features["emotion_happy"]
            - 0.7 * features["emotion_sad"]
            - 1.0 * features["emotion_angry"]
            + 0.4 * features["pose_area_ratio"]
            + 0.2 * features["pose_pc1_variance"]
            + 0.5 * features["clip_attentive_cat"]
            + 0.3 * features["clip_alert_cat"]
            + 0.2 * features["clip_playful_cat"]
        )
        predictions: dict[str, float] = {}
        for index, candidate_video_id in enumerate(candidate_video_ids, start=1):
            periodic_bias = math.sin(index) * 0.1
            predictions[candidate_video_id] = round(base_score + periodic_bias, 6)
        return predictions
