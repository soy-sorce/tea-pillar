"""Local smoke test for the model FastAPI app.

This script exercises the `/predict` route in-process via TestClient so we can
catch request-envelope and runtime import issues before building/deploying to
Cloud Run.
"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

MODEL_ROOT = Path(__file__).resolve().parents[1]

if str(MODEL_ROOT) not in sys.path:
    sys.path.insert(0, str(MODEL_ROOT))


def install_fake_predictor_module() -> None:
    """Install a lightweight predictor module for local smoke execution."""
    from src.schemas import PredictionResponse

    fake_module: Any = types.ModuleType("src.predictor")

    class Predictor:
        """Small fake predictor used to validate app wiring."""

        def predict(self: Predictor, request: object) -> PredictionResponse:
            del request
            return PredictionResponse(
                features={"emotion_happy": 0.9},
                aux_labels={
                    "emotion_label": "happy",
                    "clip_top_label": "curious_cat",
                    "meow_label": None,
                },
                predicted_rewards={"video-1": 0.5},
            )

    fake_module.Predictor = Predictor
    sys.modules["src.predictor"] = fake_module


def main() -> int:
    """Run local smoke checks against the FastAPI app."""
    install_fake_predictor_module()

    from src import app as app_module

    app_module._predictor = None
    client = TestClient(app_module.app)

    vertex_response = client.post(
        "/predict",
        json={
            "instances": [
                {
                    "image_gcs_uri": "gs://dummy-bucket/cat.jpg",
                    "audio_base64": None,
                    "candidate_video_ids": ["video-1"],
                },
            ],
        },
    )
    local_response = client.post(
        "/predict",
        json={
            "image_gcs_uri": "gs://dummy-bucket/cat.jpg",
            "audio_base64": None,
            "candidate_video_ids": ["video-1"],
        },
    )

    print("=== Vertex Envelope Response ===")
    print(json.dumps(vertex_response.json(), ensure_ascii=False, indent=2))
    print("\n=== Local Body Response ===")
    print(json.dumps(local_response.json(), ensure_ascii=False, indent=2))

    if vertex_response.status_code != 200:
        print(
            f"vertex envelope check failed: status={vertex_response.status_code}",
            file=sys.stderr,
        )
        return 1
    if local_response.status_code != 200:
        print(
            f"local body check failed: status={local_response.status_code}",
            file=sys.stderr,
        )
        return 1

    print("\nSmoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
