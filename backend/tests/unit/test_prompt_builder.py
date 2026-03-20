"""Unit tests for Gemini prompt assembly."""

from src.models.internal import CatFeatures
from src.services.gemini.prompt_builder import PromptBuilder


def test_build_includes_template_state_and_features() -> None:
    builder = PromptBuilder()
    features = CatFeatures(
        features={
            "clip_curious_cat": 0.8,
            "emotion_happy": 0.9,
        },
        emotion_label="happy",
        clip_top_label="curious_cat",
        meow_label=None,
        predicted_rewards={"video-1": 0.5},
    )

    prompt = builder.build(
        template_text="A bright moving toy crossing the frame.",
        cat_features=features,
        state_key="unknown_happy_curious_cat",
        user_context="甘えん坊で好奇心が強い",
    )

    assert "A bright moving toy crossing the frame." in prompt
    assert "unknown_happy_curious_cat" in prompt
    assert "- emotion_label: happy" in prompt
    assert "- meow_label: unknown" in prompt
    assert "- clip_curious_cat: 0.8000" in prompt
    assert "甘えん坊で好奇心が強い" in prompt


def test_build_uses_default_text_when_user_context_is_missing() -> None:
    builder = PromptBuilder()
    features = CatFeatures(
        features={"emotion_angry": 0.2},
        emotion_label="angry",
        clip_top_label="alert_cat",
        meow_label="insistent",
        predicted_rewards={"video-1": 0.2},
    )

    prompt = builder.build(
        template_text="Alert motion",
        cat_features=features,
        state_key="insistent_angry_alert_cat",
        user_context=None,
    )

    assert "（指定なし）" in prompt
    assert "- meow_label: insistent" in prompt


def test_build_sorts_feature_lines_and_includes_constraints() -> None:
    builder = PromptBuilder()
    features = CatFeatures(
        features={
            "z_feature": 0.1,
            "a_feature": 0.9,
        },
        emotion_label="happy",
        clip_top_label="curious_cat",
        meow_label="waiting_for_food",
        predicted_rewards={"video-1": 0.2},
    )

    prompt = builder.build(
        template_text="template",
        cat_features=features,
        state_key="waiting_for_food_happy_curious_cat",
        user_context=None,
    )

    assert prompt.index("- a_feature: 0.9000") < prompt.index("- z_feature: 0.1000")
    assert "あなたは猫向け動画のプロンプトクリエイターです。" in prompt
    assert "- 動画は音声なし" in prompt
