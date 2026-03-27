"""Unit tests for generate orchestrator fallback behavior."""

from __future__ import annotations

from typing import Any, Self, cast

from src.config import Settings
from src.domain.statuses import SessionMode
from src.exceptions import ModelServiceError
from src.models.firestore import TemplateDocument
from src.models.internal import BanditSelection, GenerationContext
from src.models.request import GenerateRequest
from src.services.orchestrator import GenerateOrchestrator


class FakeFirestoreClient:
    def __init__(self: Self, templates: list[TemplateDocument]) -> None:
        self.templates = templates
        self.marked_generated = False

    async def create_session(self: Self, ctx: GenerationContext) -> None:
        del ctx

    async def get_active_templates(self: Self) -> list[TemplateDocument]:
        return self.templates

    async def mark_session_generated(self: Self, ctx: GenerationContext) -> None:
        del ctx
        self.marked_generated = True

    async def fail_session(self: Self, ctx: GenerationContext, error_msg: str) -> None:
        del ctx, error_msg
        raise AssertionError("fail_session should not be called for model fallback")


class FailingCatModelClient:
    async def predict(
        self: Self,
        image_base64: str,
        audio_base64: str | None,
        candidate_video_ids: list[str],
    ) -> object:
        del image_base64, audio_base64, candidate_video_ids
        raise ModelServiceError(detail="predict failed")


class CapturingBandit:
    def __init__(self: Self) -> None:
        self.state_key: str | None = None
        self.predicted_rewards: dict[str, float] | None = None
        self.templates: list[TemplateDocument] | None = None

    async def select(
        self: Self,
        state_key: str,
        predicted_rewards: dict[str, float],
        templates: list[TemplateDocument] | None = None,
    ) -> BanditSelection:
        self.state_key = state_key
        self.predicted_rewards = predicted_rewards
        self.templates = templates
        return BanditSelection(
            template_id="video-1",
            template_name="template-1",
            prompt_text="prompt-1",
            predicted_reward=0.0,
            alpha=1.0,
            beta=1.0,
            bandit_score=0.5,
            final_score=0.5,
        )


class CapturingGeminiClient:
    def __init__(self: Self) -> None:
        self.cat_features: object | None = "unset"
        self.state_key: str | None = None

    async def generate_prompt(
        self: Self,
        template_text: str,
        cat_features: object,
        state_key: str | None,
        user_context: str | None,
    ) -> str:
        del template_text, user_context
        self.cat_features = cat_features
        self.state_key = state_key
        return "generated prompt"


class FakeVeoClient:
    async def generate(self: Self, prompt: str) -> str:
        assert prompt == "generated prompt"
        return "gs://bucket/generated/video.mp4"


class FakeSignedUrlGenerator:
    def generate(self: Self, gcs_uri: str) -> str:
        assert gcs_uri == "gs://bucket/generated/video.mp4"
        return "https://signed.example/video.mp4"


async def test_orchestrator_falls_back_when_model_service_predict_fails() -> None:
    templates = [
        TemplateDocument(
            template_id="video-1",
            name="template-1",
            prompt_text="prompt-1",
            is_active=True,
        )
    ]
    firestore = FakeFirestoreClient(templates=templates)
    bandit = CapturingBandit()
    gemini = CapturingGeminiClient()
    orchestrator = GenerateOrchestrator(
        settings=Settings(),
        firestore_client=cast(Any, firestore),
        cat_model_client=cast(Any, FailingCatModelClient()),
        bandit=cast(Any, bandit),
        gemini_client=cast(Any, gemini),
        veo_client=cast(Any, FakeVeoClient()),
        signed_url_generator=cast(Any, FakeSignedUrlGenerator()),
    )

    response = await orchestrator.execute(
        GenerateRequest(
            mode=SessionMode.EXPERIENCE,
            image_base64="encoded-image",
        )
    )

    assert response.session_id
    assert response.video_url == "https://signed.example/video.mp4"
    assert response.state_key == "fallback"
    assert response.template_id == "video-1"
    assert response.template_name == "template-1"
    assert bandit.state_key == "fallback"
    assert bandit.predicted_rewards == {}
    assert bandit.templates == templates
    assert gemini.cat_features is None
    assert gemini.state_key == "fallback"
    assert firestore.marked_generated is True
