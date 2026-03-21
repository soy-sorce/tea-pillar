"""Tests for model request envelope handling."""

from __future__ import annotations

from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from src.app import app as model_app
from src.schemas import PredictionResponse


def test_predict_accepts_vertex_instances_envelope(monkeypatch: MonkeyPatch) -> None:
    class FakePredictor:
        def predict(self: FakePredictor, request: object) -> PredictionResponse:
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

    monkeypatch.setattr("src.app._predictor", FakePredictor())

    client = TestClient(model_app)
    response = client.post(
        "/predict",
        json={
            "instances": [
                {
                    "image_gcs_uri": "gs://bucket/input.jpg",
                    "audio_base64": None,
                    "candidate_video_ids": ["video-1"],
                },
            ],
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "predictions": [
            {
                "features": {"emotion_happy": 0.9},
                "aux_labels": {
                    "emotion_label": "happy",
                    "clip_top_label": "curious_cat",
                    "meow_label": None,
                },
                "predicted_rewards": {"video-1": 0.5},
            },
        ],
    }


def test_predict_rejects_empty_instances() -> None:
    client = TestClient(model_app)
    response = client.post("/predict", json={"instances": []})

    assert response.status_code == 400
    assert response.json()["detail"] == "instances must not be empty"
