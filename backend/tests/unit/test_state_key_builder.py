"""Unit tests for the state key builder."""

from src.models.internal import CatFeatures
from src.services.state_key.builder import StateKeyBuilder


def test_build_returns_expected_format() -> None:
    builder = StateKeyBuilder()
    features = CatFeatures(
        features={"emotion_happy": 0.7},
        emotion_label="happy",
        clip_top_label="curious_cat",
        meow_label="waiting_for_food",
        predicted_rewards={"video-1": 0.1},
    )

    assert builder.build(features) == "waiting_for_food_happy_curious_cat"


def test_build_falls_back_to_unknown_meow_label() -> None:
    builder = StateKeyBuilder()
    features = CatFeatures(
        features={"emotion_sad": 0.8},
        emotion_label="sad",
        clip_top_label="sleepy_cat",
        meow_label=None,
        predicted_rewards={"video-1": 0.1},
    )

    assert builder.build(features) == "unknown_sad_sleepy_cat"
