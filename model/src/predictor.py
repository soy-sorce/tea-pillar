"""Local predictor entrypoint and reusable prediction service."""

from __future__ import annotations

import json
import sys
from typing import Self

from src.artifacts import load_artifacts
from src.feature_extractor import FeatureExtractor
from src.regressor import RewardRegressor
from src.schemas import PredictionRequest, PredictionResponse


class Predictor:
    """Contract-compatible predictor."""

    def __init__(self: Self) -> None:
        self._artifacts = load_artifacts()
        self._feature_extractor = FeatureExtractor()
        self._regressor = RewardRegressor(artifacts=self._artifacts)

    def predict(self: Self, request: PredictionRequest) -> PredictionResponse:
        """Run feature extraction and reward prediction."""
        features, aux_labels = self._feature_extractor.extract(request=request)
        predicted_rewards = self._regressor.predict(
            features=features,
            candidate_video_ids=request.candidate_video_ids,
        )
        return PredictionResponse(
            features=features,
            aux_labels=aux_labels,
            predicted_rewards=predicted_rewards,
        )


def main() -> None:
    """Read a request JSON from stdin and write a response JSON to stdout."""
    payload = json.load(sys.stdin)
    request = PredictionRequest(
        image_base64=str(payload["image_base64"]),
        audio_base64=(
            str(payload["audio_base64"]) if payload.get("audio_base64") is not None else None
        ),
        candidate_video_ids=[str(item) for item in payload["candidate_video_ids"]],
    )
    response = Predictor().predict(request=request)
    json.dump(response.to_dict(), sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
