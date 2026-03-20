"""Unit tests for request and response schemas."""

from __future__ import annotations

from pydantic import ValidationError
from src.models.request import FeedbackRequest, GenerateRequest
from src.models.response import GenerateResponse


def test_generate_request_accepts_valid_values() -> None:
    request = GenerateRequest(
        mode="experience",
        image_base64="encoded",
        audio_base64=None,
        user_context="curious cat",
    )

    assert request.mode == "experience"
    assert request.image_base64 == "encoded"


def test_generate_request_rejects_invalid_mode() -> None:
    try:
        GenerateRequest.model_validate({"mode": "invalid", "image_base64": "encoded"})
    except ValidationError as exc:
        assert "experience" in str(exc)
        assert "production" in str(exc)
    else:
        raise AssertionError("ValidationError was not raised")


def test_generate_request_rejects_empty_image_base64() -> None:
    try:
        GenerateRequest(mode="production", image_base64="")
    except ValidationError as exc:
        assert "at least 1 character" in str(exc)
    else:
        raise AssertionError("ValidationError was not raised")


def test_generate_request_rejects_too_long_user_context() -> None:
    try:
        GenerateRequest(
            mode="production",
            image_base64="encoded",
            user_context="x" * 501,
        )
    except ValidationError as exc:
        assert "at most 500 characters" in str(exc)
    else:
        raise AssertionError("ValidationError was not raised")


def test_feedback_request_rejects_invalid_reaction() -> None:
    try:
        FeedbackRequest.model_validate({"session_id": "session-1", "reaction": "great"})
    except ValidationError as exc:
        assert "good" in str(exc)
        assert "neutral" in str(exc)
        assert "bad" in str(exc)
    else:
        raise AssertionError("ValidationError was not raised")


def test_feedback_request_rejects_empty_session_id() -> None:
    try:
        FeedbackRequest(session_id="", reaction="good")
    except ValidationError as exc:
        assert "at least 1 character" in str(exc)
    else:
        raise AssertionError("ValidationError was not raised")


def test_generate_response_contains_required_fields() -> None:
    response = GenerateResponse(
        session_id="session-1",
        video_url="https://example.com/video.mp4",
        state_key="unknown_happy_curious_cat",
        template_id="video-1",
        template_name="mouse chase",
    )

    assert response.model_dump() == {
        "session_id": "session-1",
        "video_url": "https://example.com/video.mp4",
        "state_key": "unknown_happy_curious_cat",
        "template_id": "video-1",
        "template_name": "mouse chase",
    }
