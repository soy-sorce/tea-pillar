"""Tests for model service routes."""

from __future__ import annotations

from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from src.app import app as model_app
from src.dependencies import _predictor
from src.schemas import PredictionResponse, RewardAnalysisResponse


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

    monkeypatch.setattr("src.dependencies._predictor", FakePredictor())

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


def test_root_returns_service_descriptor(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr("src.dependencies._predictor", _predictor)
    client = TestClient(model_app)

    response = client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "nekkoflix-model"
    assert body["status"] == "ok"
    assert body["predict_endpoint"] == "/predict"
    assert body["reward_analysis_endpoint"] == "/analyze-reward"


def test_analyze_reward_returns_metrics(monkeypatch: MonkeyPatch) -> None:
    class FakeRewardAnalyzer:
        def analyze(self: FakeRewardAnalyzer, request: object) -> RewardAnalysisResponse:
            del request
            return RewardAnalysisResponse(
                paw_hit_count=2,
                gaze_duration_seconds=4.25,
                reward=0.8125,
                analysis_model_versions={
                    "paw_detector": "fake-v1",
                    "gaze_estimator": "fake-v1",
                },
            )

    monkeypatch.setattr("src.dependencies._reward_analyzer", FakeRewardAnalyzer())
    client = TestClient(model_app)

    response = client.post(
        "/analyze-reward",
        json={
            "reaction_video_gcs_uri": "gs://bucket/reaction.mp4",
            "session_id": "session-1",
            "template_id": "video-1",
            "state_key": "happy_clip-a",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "paw_hit_count": 2,
        "gaze_duration_seconds": 4.25,
        "reward": 0.8125,
        "analysis_model_versions": {
            "paw_detector": "fake-v1",
            "gaze_estimator": "fake-v1",
        },
    }


def test_analyze_reward_rejects_missing_uri() -> None:
    client = TestClient(model_app)
    response = client.post("/analyze-reward", json={})

    assert response.status_code == 400
    assert response.json()["detail"] == "reaction_video_gcs_uri must be a non-empty string"
