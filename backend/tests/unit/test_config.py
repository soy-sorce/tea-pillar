"""Unit tests for application settings."""

from __future__ import annotations

from pytest import MonkeyPatch
from src.config import Settings, get_settings


def test_settings_defaults_match_expected_values() -> None:
    settings = Settings()

    assert settings.gcp_region == "asia-northeast1"
    assert settings.vertex_prediction_timeout == 30
    assert settings.gemini_model == "gemini-1.5-flash"
    assert settings.veo_model == "veo-3.1-fast"
    assert settings.bandit_ucb_alpha == 1.0


def test_default_candidate_video_ids_cover_video_1_to_10() -> None:
    settings = Settings()

    assert settings.default_candidate_video_ids == [
        "video-1",
        "video-2",
        "video-3",
        "video-4",
        "video-5",
        "video-6",
        "video-7",
        "video-8",
        "video-9",
        "video-10",
    ]


def test_settings_environment_variables_override_defaults(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_MODEL", "gemini-test")
    monkeypatch.setenv("BANDIT_UCB_ALPHA", "2.5")

    settings = Settings()

    assert settings.gemini_model == "gemini-test"
    assert settings.bandit_ucb_alpha == 2.5


def test_get_settings_is_cached() -> None:
    get_settings.cache_clear()

    first = get_settings()
    second = get_settings()

    assert first is second

    get_settings.cache_clear()
