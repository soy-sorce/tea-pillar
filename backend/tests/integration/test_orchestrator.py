"""Integration-style tests for GenerateOrchestrator with fake dependencies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

import pytest
from src.config import Settings
from src.exceptions import (
    FirestoreError,
    GeminiError,
    NotConfiguredError,
    TemplateSelectionError,
    VeoGenerationError,
    VeoTimeoutError,
    VertexAIError,
)
from src.models.firestore import TemplateDocument
from src.models.internal import BanditSelection, CatFeatures, GenerationContext
from src.models.request import GenerateRequest
from src.services.orchestrator import GenerateOrchestrator


@dataclass
class FakeFirestore:
    created: GenerationContext | None = None
    completed: GenerationContext | None = None
    failed: tuple[GenerationContext, str] | None = None

    async def create_session(self: Self, ctx: GenerationContext) -> None:
        self.created = ctx

    async def complete_session(self: Self, ctx: GenerationContext) -> None:
        self.completed = ctx

    async def fail_session(self: Self, ctx: GenerationContext, error_msg: str) -> None:
        self.failed = (ctx, error_msg)


class FailingFailFirestore(FakeFirestore):
    async def fail_session(self: Self, ctx: GenerationContext, error_msg: str) -> None:
        del ctx, error_msg
        raise FirestoreError(detail="cannot persist failure")


class FakeCatModelClient:
    async def predict(
        self: Self,
        image_base64: str,
        audio_base64: str | None,
        candidate_video_ids: list[str],
    ) -> CatFeatures:
        assert image_base64 == "encoded-image"
        assert audio_base64 == "encoded-audio"
        assert candidate_video_ids[0] == "video-1"
        return CatFeatures(
            features={"emotion_happy": 0.9, "clip_curious_cat": 0.8},
            emotion_label="happy",
            clip_top_label="curious_cat",
            meow_label=None,
            predicted_rewards={"video-1": 0.3, "video-2": 0.2},
        )


class FakeBandit:
    async def select(
        self: Self,
        state_key: str,
        predicted_rewards: dict[str, float],
    ) -> BanditSelection:
        assert state_key == "unknown_happy_curious_cat"
        assert predicted_rewards["video-1"] == 0.3
        return BanditSelection(
            template_id="video-1",
            template_name="mouse escape chase",
            prompt_text="mouse chasing prompt",
            predicted_reward=0.3,
            ucb_bonus=0.1,
            final_score=0.4,
        )


class FakeGemini:
    async def generate_prompt(
        self: Self,
        template_text: str,
        cat_features: CatFeatures | None,
        state_key: str | None,
        user_context: str | None,
    ) -> str:
        assert template_text == "mouse chasing prompt"
        assert cat_features is not None
        assert cat_features.emotion_label == "happy"
        assert state_key == "unknown_happy_curious_cat"
        assert user_context == "curious"
        return "final veo prompt"


class FakeVeo:
    async def generate(self: Self, prompt: str) -> str:
        assert prompt == "final veo prompt"
        return "gs://bucket/generated/video.mp4"


class FakeSignedUrlGenerator:
    def generate(self: Self, gcs_uri: str) -> str:
        assert gcs_uri == "gs://bucket/generated/video.mp4"
        return "https://signed.example/video.mp4"


async def test_execute_returns_final_generate_response() -> None:
    firestore = FakeFirestore()
    orchestrator = GenerateOrchestrator(
        settings=Settings(),
        firestore_client=firestore,  # type: ignore[arg-type]
        cat_model_client=FakeCatModelClient(),  # type: ignore[arg-type]
        bandit=FakeBandit(),  # type: ignore[arg-type]
        gemini_client=FakeGemini(),  # type: ignore[arg-type]
        veo_client=FakeVeo(),  # type: ignore[arg-type]
        signed_url_generator=FakeSignedUrlGenerator(),  # type: ignore[arg-type]
    )

    response = await orchestrator.execute(
        GenerateRequest(
            mode="experience",
            image_base64="encoded-image",
            audio_base64="encoded-audio",
            user_context="curious",
        ),
    )

    assert response.template_id == "video-1"
    assert response.template_name == "mouse escape chase"
    assert response.state_key == "unknown_happy_curious_cat"
    assert response.video_url == "https://signed.example/video.mp4"
    assert firestore.created is not None
    assert firestore.completed is not None
    assert firestore.failed is None
    assert firestore.created.session_id == response.session_id
    assert firestore.completed.state_key == "unknown_happy_curious_cat"


class FailingCatModelClient:
    async def predict(
        self: Self,
        image_base64: str,
        audio_base64: str | None,
        candidate_video_ids: list[str],
    ) -> CatFeatures:
        raise VertexAIError(detail="endpoint failed")


class TemplateSelectionFailingBandit:
    async def select(
        self: Self,
        state_key: str,
        predicted_rewards: dict[str, float],
    ) -> BanditSelection:
        del state_key, predicted_rewards
        raise TemplateSelectionError(detail="template failed")


async def test_execute_marks_session_failed_when_non_fallback_service_raises() -> None:
    firestore = FakeFirestore()
    orchestrator = GenerateOrchestrator(
        settings=Settings(),
        firestore_client=firestore,  # type: ignore[arg-type]
        cat_model_client=FakeCatModelClient(),  # type: ignore[arg-type]
        bandit=TemplateSelectionFailingBandit(),  # type: ignore[arg-type]
    )

    with pytest.raises(TemplateSelectionError):
        await orchestrator.execute(
            GenerateRequest(
                mode="experience",
                image_base64="encoded-image",
                audio_base64=None,
                user_context=None,
            ),
        )

    assert firestore.created is not None
    assert firestore.failed is not None
    assert firestore.failed[1] == "template failed"


@pytest.mark.parametrize(
    ("exception", "expected_detail"),
    [
        (TemplateSelectionError(detail="template failed"), "template failed"),
        (GeminiError(detail="gemini failed"), "gemini failed"),
        (VeoGenerationError(detail="veo failed"), "veo failed"),
        (VeoTimeoutError(detail="veo timeout"), "veo timeout"),
        (NotConfiguredError(detail="missing config"), "missing config"),
    ],
)
async def test_execute_marks_session_failed_for_all_handled_errors(
    exception: Exception,
    expected_detail: str,
) -> None:
    class FailingDependency:
        async def select(
            self: Self, state_key: str, predicted_rewards: dict[str, float]
        ) -> BanditSelection:
            del state_key, predicted_rewards
            raise exception

    firestore = FakeFirestore()
    orchestrator = GenerateOrchestrator(
        settings=Settings(),
        firestore_client=firestore,  # type: ignore[arg-type]
        cat_model_client=FakeCatModelClient(),  # type: ignore[arg-type]
        bandit=FailingDependency(),  # type: ignore[arg-type]
    )

    with pytest.raises(type(exception)):
        await orchestrator.execute(
            GenerateRequest(
                mode="experience",
                image_base64="encoded-image",
                audio_base64=None,
                user_context=None,
            ),
        )

    assert firestore.failed is not None
    assert firestore.failed[1] == expected_detail


async def test_execute_reraises_original_error_when_fail_session_also_fails() -> None:
    orchestrator = GenerateOrchestrator(
        settings=Settings(),
        firestore_client=FailingFailFirestore(),  # type: ignore[arg-type]
        cat_model_client=FakeCatModelClient(),  # type: ignore[arg-type]
        bandit=TemplateSelectionFailingBandit(),  # type: ignore[arg-type]
    )

    with pytest.raises(TemplateSelectionError):
        await orchestrator.execute(
            GenerateRequest(
                mode="experience",
                image_base64="encoded-image",
                audio_base64=None,
                user_context=None,
            ),
        )


async def test_execute_forwards_none_audio_and_user_context() -> None:
    captured: dict[str, object] = {}

    class NoAudioCatModelClient:
        async def predict(
            self: Self,
            image_base64: str,
            audio_base64: str | None,
            candidate_video_ids: list[str],
        ) -> CatFeatures:
            captured["image_base64"] = image_base64
            captured["audio_base64"] = audio_base64
            captured["candidate_video_ids"] = candidate_video_ids
            return CatFeatures(
                features={"emotion_happy": 0.9},
                emotion_label="happy",
                clip_top_label="curious_cat",
                meow_label=None,
                predicted_rewards={"video-1": 0.3},
            )

    class SingleBandit:
        async def select(
            self: Self, state_key: str, predicted_rewards: dict[str, float]
        ) -> BanditSelection:
            del predicted_rewards
            captured["state_key"] = state_key
            return BanditSelection(
                template_id="video-1",
                template_name="mouse escape chase",
                prompt_text="mouse chasing prompt",
                predicted_reward=0.3,
                ucb_bonus=0.0,
                final_score=0.3,
            )

    class RecordingGemini:
        async def generate_prompt(
            self: Self,
            template_text: str,
            cat_features: CatFeatures | None,
            state_key: str | None,
            user_context: str | None,
        ) -> str:
            del template_text, cat_features, state_key
            captured["user_context"] = user_context
            return "final veo prompt"

    orchestrator = GenerateOrchestrator(
        settings=Settings(),
        firestore_client=FakeFirestore(),  # type: ignore[arg-type]
        cat_model_client=NoAudioCatModelClient(),  # type: ignore[arg-type]
        bandit=SingleBandit(),  # type: ignore[arg-type]
        gemini_client=RecordingGemini(),  # type: ignore[arg-type]
        veo_client=FakeVeo(),  # type: ignore[arg-type]
        signed_url_generator=FakeSignedUrlGenerator(),  # type: ignore[arg-type]
    )

    response = await orchestrator.execute(
        GenerateRequest(
            mode="production",
            image_base64="encoded-image",
            audio_base64=None,
            user_context=None,
        ),
    )

    assert response.template_id == "video-1"
    assert captured["audio_base64"] is None
    assert captured["user_context"] is None


class FixedFallbackTemplateLoader:
    def get_random_template(self: Self) -> TemplateDocument:
        return TemplateDocument(
            template_id="video-7",
            name="cat tower across screen",
            prompt_text="A cat reaching a paw across the screen boundary.",
            is_active=True,
            auto_generated=False,
        )


async def test_execute_uses_fallback_template_when_vertex_fails() -> None:
    firestore = FakeFirestore()
    captured: dict[str, object] = {}

    class FallbackGemini:
        async def generate_prompt(
            self: Self,
            template_text: str,
            cat_features: CatFeatures | None,
            state_key: str | None,
            user_context: str | None,
        ) -> str:
            captured["template_text"] = template_text
            captured["cat_features"] = cat_features
            captured["state_key"] = state_key
            captured["user_context"] = user_context
            return "fallback veo prompt"

    class FallbackVeo:
        async def generate(self: Self, prompt: str) -> str:
            assert prompt == "fallback veo prompt"
            return "gs://bucket/generated/video.mp4"

    orchestrator = GenerateOrchestrator(
        settings=Settings(),
        firestore_client=firestore,  # type: ignore[arg-type]
        cat_model_client=FailingCatModelClient(),  # type: ignore[arg-type]
        gemini_client=FallbackGemini(),  # type: ignore[arg-type]
        veo_client=FallbackVeo(),  # type: ignore[arg-type]
        signed_url_generator=FakeSignedUrlGenerator(),  # type: ignore[arg-type]
        fallback_template_loader=FixedFallbackTemplateLoader(),  # type: ignore[arg-type]
    )

    response = await orchestrator.execute(
        GenerateRequest(
            mode="experience",
            image_base64="encoded-image",
            audio_base64=None,
            user_context="playful",
        ),
    )

    assert response.template_id == "video-7"
    assert response.template_name == "cat tower across screen"
    assert response.state_key == ""
    assert response.video_url == "https://signed.example/video.mp4"
    assert captured["template_text"] == "A cat reaching a paw across the screen boundary."
    assert captured["cat_features"] is None
    assert captured["state_key"] is None
    assert captured["user_context"] == "playful"
    assert firestore.completed is not None
    assert firestore.completed.fallback_used is True
    assert firestore.failed is None
