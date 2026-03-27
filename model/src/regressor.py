"""Reward regressor runtime."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol, Self, cast

import numpy as np
import pandas as pd

from .artifacts import ArtifactBundle


class _Predictor(Protocol):
    def predict(self: Self, frame: object) -> Iterable[object]: ...


class RewardRegressor:
    """Predict expected reward for each candidate template."""

    def __init__(self: Self, artifacts: ArtifactBundle | None) -> None:
        self._artifacts = artifacts

    def predict(
        self: Self,
        *,
        features: dict[str, float],
        candidate_video_ids: list[str],
    ) -> dict[str, float]:
        """Predict expected reward for the supplied candidate ids."""
        if self._artifacts is None:
            return {candidate_video_id: 0.0 for candidate_video_id in candidate_video_ids}

        rows = []
        for candidate_video_id in candidate_video_ids:
            row = {name: 0.0 for name in self._artifacts.feature_columns}
            for key, value in features.items():
                if key in row:
                    row[key] = float(value)
            video_column = f"video_{candidate_video_id}"
            if video_column in row:
                row[video_column] = 1.0
            rows.append(row)

        frame = pd.DataFrame(rows, columns=self._artifacts.feature_columns).fillna(0.0)
        predictor = cast(_Predictor, self._artifacts.regressor)
        predictions = predictor.predict(frame)
        if isinstance(predictions, np.ndarray):
            values = predictions.tolist()
        else:
            values = list(predictions)
        return {
            candidate_video_id: float(value)
            for candidate_video_id, value in zip(candidate_video_ids, values, strict=True)
        }
