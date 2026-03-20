"""Unit tests for the Gemini client."""

from __future__ import annotations

from collections.abc import Awaitable

from google.api_core.exceptions import DeadlineExceeded, GoogleAPICallError, RetryError
from pytest import MonkeyPatch
from src.config import Settings
from src.exceptions import GeminiError, NotConfiguredError
from src.models.internal import CatFeatures
from src.services.gemini.client import GeminiClient


def _features() -> CatFeatures:
    return CatFeatures(
        features={"emotion_happy": 0.9},
        emotion_label="happy",
        clip_top_label="curious_cat",
        meow_label=None,
        predicted_rewards={"video-1": 0.1},
    )


async def test_generate_prompt_raises_when_not_configured() -> None:
    client = GeminiClient(settings=Settings(gcp_project_id=""))

    try:
        await client.generate_prompt("template", _features(), "state", None)
    except NotConfiguredError as exc:
        assert exc.error_code == "NOT_CONFIGURED"
    else:
        raise AssertionError("NotConfiguredError was not raised")


async def test_generate_prompt_calls_model_and_returns_stripped_text(
    monkeypatch: MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeModel:
        def __init__(self, model_name: str) -> None:
            captured["model_name"] = model_name

        async def generate_content_async(
            self,
            prompt: str,
            generation_config: dict[str, object],
        ) -> object:
            captured["prompt"] = prompt
            captured["generation_config"] = generation_config
            return type("Response", (), {"text": " final prompt \n"})()

    monkeypatch.setattr(
        "src.services.gemini.client.vertexai.init", lambda **kwargs: captured.update(kwargs)
    )
    monkeypatch.setattr("src.services.gemini.client.GenerativeModel", FakeModel)

    client = GeminiClient(
        settings=Settings(gcp_project_id="demo-project", gemini_model="gemini-test")
    )
    prompt = await client.generate_prompt("template", _features(), "state-key", "owner context")

    assert prompt == "final prompt"
    assert captured["project"] == "demo-project"
    assert captured["location"] == "asia-northeast1"
    assert captured["model_name"] == "gemini-test"
    assert isinstance(captured["prompt"], str)
    assert captured["generation_config"] == {"max_output_tokens": 512, "temperature": 0.7}


async def test_generate_prompt_maps_timeout_error(monkeypatch: MonkeyPatch) -> None:
    class FakeModel:
        def __init__(self, model_name: str) -> None:
            del model_name

        async def generate_content_async(
            self,
            prompt: str,
            generation_config: dict[str, object],
        ) -> object:
            del prompt, generation_config
            raise TimeoutError("timed out")

    async def fake_wait_for(awaitable: Awaitable[object], timeout: object) -> object:
        del timeout
        return await awaitable

    monkeypatch.setattr("src.services.gemini.client.vertexai.init", lambda **kwargs: None)
    monkeypatch.setattr("src.services.gemini.client.GenerativeModel", FakeModel)
    monkeypatch.setattr("src.services.gemini.client.asyncio.wait_for", fake_wait_for)

    client = GeminiClient(settings=Settings(gcp_project_id="demo"))

    try:
        await client.generate_prompt("template", _features(), "state", None)
    except GeminiError as exc:
        assert exc.error_code == "GEMINI_FAILED"
        assert "タイムアウト" in exc.message
    else:
        raise AssertionError("GeminiError was not raised")


async def test_generate_prompt_maps_deadline_exceeded(monkeypatch: MonkeyPatch) -> None:
    class FakeModel:
        def __init__(self, model_name: str) -> None:
            del model_name

        async def generate_content_async(
            self,
            prompt: str,
            generation_config: dict[str, object],
        ) -> object:
            del prompt, generation_config
            raise DeadlineExceeded("timed out")

    monkeypatch.setattr("src.services.gemini.client.vertexai.init", lambda **kwargs: None)
    monkeypatch.setattr("src.services.gemini.client.GenerativeModel", FakeModel)

    client = GeminiClient(settings=Settings(gcp_project_id="demo"))

    try:
        await client.generate_prompt("template", _features(), "state", None)
    except GeminiError as exc:
        assert exc.error_code == "GEMINI_FAILED"
    else:
        raise AssertionError("GeminiError was not raised")


async def test_generate_prompt_maps_retry_error(monkeypatch: MonkeyPatch) -> None:
    retry_error = RetryError("timed out", cause=ValueError("cause"))

    class FakeModel:
        def __init__(self, model_name: str) -> None:
            del model_name

        async def generate_content_async(
            self,
            prompt: str,
            generation_config: dict[str, object],
        ) -> object:
            del prompt, generation_config
            raise retry_error

    monkeypatch.setattr("src.services.gemini.client.vertexai.init", lambda **kwargs: None)
    monkeypatch.setattr("src.services.gemini.client.GenerativeModel", FakeModel)

    client = GeminiClient(settings=Settings(gcp_project_id="demo"))

    try:
        await client.generate_prompt("template", _features(), "state", None)
    except GeminiError as exc:
        assert exc.error_code == "GEMINI_FAILED"
    else:
        raise AssertionError("GeminiError was not raised")


async def test_generate_prompt_maps_google_api_error(monkeypatch: MonkeyPatch) -> None:
    class FakeModel:
        def __init__(self, model_name: str) -> None:
            del model_name

        async def generate_content_async(
            self,
            prompt: str,
            generation_config: dict[str, object],
        ) -> object:
            del prompt, generation_config
            raise GoogleAPICallError("boom")

    monkeypatch.setattr("src.services.gemini.client.vertexai.init", lambda **kwargs: None)
    monkeypatch.setattr("src.services.gemini.client.GenerativeModel", FakeModel)

    client = GeminiClient(settings=Settings(gcp_project_id="demo"))

    try:
        await client.generate_prompt("template", _features(), "state", None)
    except GeminiError as exc:
        assert exc.error_code == "GEMINI_FAILED"
    else:
        raise AssertionError("GeminiError was not raised")
