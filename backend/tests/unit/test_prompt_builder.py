"""Unit tests for Gemini prompt assembly."""

from src.models.internal import CatFeatures
from src.services.gemini.prompt_builder import PromptBuilder


def test_build_uses_only_template_context_and_constraints() -> None:
    builder = PromptBuilder()
    features = CatFeatures(
        features={
            "clip_curious_cat": 0.8,
            "emotion_happy": 0.9,
        },
        emotion_label="happy",
        clip_top_label="curious_cat",
        meow_label=None,
    )

    prompt = builder.build(
        template_text="A bright moving toy crossing the frame.",
        cat_features=features,
        state_key="unknown_happy_curious_cat",
        user_context="Very affectionate and highly curious.",
    )

    assert "A bright moving toy crossing the frame." in prompt
    assert "Very affectionate and highly curious." in prompt
    assert "[Template Query]" in prompt
    assert "[Owner Context]" in prompt
    assert "[Constraints]" in prompt
    assert "unknown_happy_curious_cat" not in prompt
    assert "emotion_label" not in prompt
    assert "clip_curious_cat" not in prompt
    assert "meow_label" not in prompt


def test_build_uses_default_text_when_user_context_is_missing() -> None:
    builder = PromptBuilder()
    features = CatFeatures(
        features={"emotion_angry": 0.2},
        emotion_label="angry",
        clip_top_label="alert_cat",
        meow_label="insistent",
    )

    prompt = builder.build(
        template_text="Alert motion",
        cat_features=features,
        state_key="insistent_angry_alert_cat",
        user_context=None,
    )

    assert "none" in prompt


def test_build_includes_constraints_even_when_cat_features_exist() -> None:
    builder = PromptBuilder()
    features = CatFeatures(
        features={
            "z_feature": 0.1,
            "a_feature": 0.9,
        },
        emotion_label="happy",
        clip_top_label="curious_cat",
        meow_label="waiting_for_food",
    )

    prompt = builder.build(
        template_text="template",
        cat_features=features,
        state_key="waiting_for_food_happy_curious_cat",
        user_context=None,
    )

    assert "You create exactly one video prompt for a cat-focused video." in prompt
    assert "- silent video" in prompt
    assert "z_feature" not in prompt
    assert "a_feature" not in prompt
    assert "waiting_for_food_happy_curious_cat" not in prompt


def test_build_supports_missing_cat_features_without_fallback_prompt() -> None:
    builder = PromptBuilder()

    prompt = builder.build(
        template_text="A glowing toy floating in the air.",
        cat_features=None,
        state_key=None,
        user_context=None,
    )

    assert "A glowing toy floating in the air." in prompt
    assert "[Template Query]" in prompt
    assert "[Owner Context]" in prompt
    assert "none" in prompt
    assert "[Constraints]" in prompt
    assert "state key" not in prompt
    assert "emotion_label" not in prompt
