"""Generation orchestrator."""

import uuid
from typing import Self

import structlog

from src.config import Settings
from src.exceptions import (
    FirestoreError,
    GeminiError,
    NekkoflixBaseError,
    NotConfiguredError,
    TemplateSelectionError,
    VeoGenerationError,
    VeoTimeoutError,
    VertexAIError,
    VertexAITimeoutError,
)
from src.models.internal import GenerationContext
from src.models.request import GenerateRequest
from src.models.response import GenerateResponse
from src.services.bandit.ucb import UCBBandit
from src.services.cat_model.client import CatModelClient
from src.services.fallback_templates.loader import FallbackTemplateLoader
from src.services.firestore.client import FirestoreClient
from src.services.gemini.client import GeminiClient
from src.services.state_key.builder import StateKeyBuilder
from src.services.veo.client import VeoClient
from src.services.veo.signed_url import SignedUrlGenerator

logger = structlog.get_logger(__name__)


class GenerateOrchestrator:
    """Coordinate the full /generate workflow."""

    def __init__(
        self: Self,
        settings: Settings,
        *,
        firestore_client: FirestoreClient | None = None,
        cat_model_client: CatModelClient | None = None,
        state_key_builder: StateKeyBuilder | None = None,
        bandit: UCBBandit | None = None,
        gemini_client: GeminiClient | None = None,
        veo_client: VeoClient | None = None,
        signed_url_generator: SignedUrlGenerator | None = None,
        fallback_template_loader: FallbackTemplateLoader | None = None,
    ) -> None:
        self._settings = settings
        self._firestore = firestore_client or FirestoreClient(settings=settings)
        self._cat_model = cat_model_client or CatModelClient(settings=settings)
        self._state_key_builder = state_key_builder or StateKeyBuilder()
        self._bandit = bandit or UCBBandit(settings=settings, firestore_client=self._firestore)
        self._gemini = gemini_client or GeminiClient(settings=settings)
        self._veo = veo_client or VeoClient(settings=settings)
        self._signed_url_generator = signed_url_generator or SignedUrlGenerator(
            settings=settings,
        )
        self._fallback_template_loader = fallback_template_loader or FallbackTemplateLoader()

    async def execute(self: Self, request: GenerateRequest) -> GenerateResponse:
        """Run the generation pipeline and return the final payload."""
        ctx = GenerationContext(
            session_id=str(uuid.uuid4()),
            mode=request.mode,
            image_base64=request.image_base64,
            audio_base64=request.audio_base64,
            user_context=request.user_context,
        )
        logger.info(
            "generate_start",
            session_id=ctx.session_id,
            mode=ctx.mode,
            has_audio=ctx.audio_base64 is not None,
            has_user_context=ctx.user_context is not None,
            candidate_count=len(self._settings.default_candidate_video_ids),
        )
        logger.debug(
            "generate_request_detail",
            session_id=ctx.session_id,
            image_length=len(ctx.image_base64),
            audio_length=len(ctx.audio_base64) if ctx.audio_base64 is not None else 0,
            user_context_preview=(ctx.user_context or "")[:300],
            candidate_video_ids=self._settings.default_candidate_video_ids,
        )

        try:
            await self._firestore.create_session(ctx=ctx)
            await self._prepare_generation_context(ctx)
            ctx.generated_prompt = await self._gemini.generate_prompt(
                template_text=ctx.bandit_selection.prompt_text,
                cat_features=ctx.cat_features,
                state_key=ctx.state_key,
                user_context=ctx.user_context,
            )
            logger.info(
                "prompt_ready",
                session_id=ctx.session_id,
                template_id=ctx.bandit_selection.template_id,
                prompt_length=len(ctx.generated_prompt),
            )
            ctx.video_gcs_uri = await self._veo.generate(prompt=ctx.generated_prompt)
            ctx.video_signed_url = self._signed_url_generator.generate(
                gcs_uri=ctx.video_gcs_uri,
            )
            await self._firestore.complete_session(ctx=ctx)
        except (
            FirestoreError,
            GeminiError,
            NotConfiguredError,
            TemplateSelectionError,
            VertexAIError,
            VertexAITimeoutError,
            VeoGenerationError,
            VeoTimeoutError,
        ) as exc:
            logger.error(
                "generate_failed",
                session_id=ctx.session_id,
                state_key=ctx.state_key,
                template_id=ctx.bandit_selection.template_id if ctx.bandit_selection else None,
                error_code=exc.error_code,
                detail=exc.detail,
            )
            logger.debug(
                "generate_failed_context",
                session_id=ctx.session_id,
                mode=ctx.mode,
                state_key=ctx.state_key,
                template_id=ctx.bandit_selection.template_id if ctx.bandit_selection else None,
                video_gcs_uri=ctx.video_gcs_uri,
                has_signed_url=ctx.video_signed_url is not None,
            )
            await self._safely_fail_session(ctx=ctx, exc=exc)
            raise

        logger.info(
            "generate_completed",
            session_id=ctx.session_id,
            state_key=ctx.state_key,
            template_id=ctx.bandit_selection.template_id if ctx.bandit_selection else None,
            video_gcs_uri=ctx.video_gcs_uri,
        )

        return GenerateResponse(
            session_id=ctx.session_id,
            video_url=ctx.video_signed_url or "",
            state_key=ctx.state_key or "",
            template_id=ctx.bandit_selection.template_id if ctx.bandit_selection else "",
            template_name=ctx.bandit_selection.template_name if ctx.bandit_selection else "",
        )

    async def _prepare_generation_context(self: Self, ctx: GenerationContext) -> None:
        """Populate the context for either normal generation or fallback generation."""
        try:
            ctx.cat_features = await self._cat_model.predict(
                image_base64=ctx.image_base64,
                audio_base64=ctx.audio_base64,
                candidate_video_ids=self._settings.default_candidate_video_ids,
            )
        except Exception as exc:
            self._apply_vertex_fallback(ctx=ctx, exc=exc)
            return

        assert ctx.cat_features is not None
        logger.info(
            "cat_features_ready",
            session_id=ctx.session_id,
            emotion_label=ctx.cat_features.emotion_label,
            clip_top_label=ctx.cat_features.clip_top_label,
            meow_label=ctx.cat_features.meow_label or "unknown",
            predicted_reward_count=len(ctx.cat_features.predicted_rewards),
        )
        ctx.state_key = self._state_key_builder.build(features=ctx.cat_features)
        logger.info(
            "state_key_ready",
            session_id=ctx.session_id,
            state_key=ctx.state_key,
        )
        ctx.bandit_selection = await self._bandit.select(
            state_key=ctx.state_key,
            predicted_rewards=ctx.cat_features.predicted_rewards,
        )
        logger.info(
            "bandit_selection_ready",
            session_id=ctx.session_id,
            state_key=ctx.state_key,
            template_id=ctx.bandit_selection.template_id,
            template_name=ctx.bandit_selection.template_name,
            predicted_reward=ctx.bandit_selection.predicted_reward,
            ucb_bonus=ctx.bandit_selection.ucb_bonus,
            final_score=ctx.bandit_selection.final_score,
        )

    def _apply_vertex_fallback(
        self: Self,
        ctx: GenerationContext,
        exc: Exception,
    ) -> None:
        """Switch to template-only generation when Vertex is unavailable."""
        template = self._fallback_template_loader.get_random_template()
        ctx.fallback_used = True
        ctx.state_key = None
        ctx.cat_features = None
        ctx.bandit_selection = BanditSelection(
            template_id=template.template_id,
            template_name=template.name,
            prompt_text=template.prompt_text,
            predicted_reward=0.0,
            ucb_bonus=0.0,
            final_score=0.0,
        )
        logger.warning(
            "vertex_fallback_activated",
            session_id=ctx.session_id,
            error_code=(
                exc.error_code if isinstance(exc, NekkoflixBaseError) else type(exc).__name__
            ),
            detail=(exc.detail if isinstance(exc, NekkoflixBaseError) else str(exc)),
            fallback_template_id=template.template_id,
            fallback_template_name=template.name,
        )

    async def _safely_fail_session(
        self: Self,
        ctx: GenerationContext,
        exc: NekkoflixBaseError,
    ) -> None:
        """Best-effort session failure persistence."""
        try:
            await self._firestore.fail_session(
                ctx=ctx,
                error_msg=exc.detail or str(exc),
            )
            logger.info(
                "session_marked_failed",
                session_id=ctx.session_id,
                error_code=exc.error_code,
            )
        except FirestoreError:
            logger.error(
                "session_fail_persist_failed",
                session_id=ctx.session_id,
                original_error=exc.error_code,
            )
