"""Generation orchestrator."""

from __future__ import annotations

import uuid
from typing import Self

from src.config import Settings
from src.exceptions import (
    FirestoreError,
    GeminiError,
    ModelServiceError,
    ModelServiceTimeoutError,
    NekkoflixBaseError,
    TemplateSelectionError,
    VeoGenerationError,
    VeoTimeoutError,
)
from src.models.internal import GenerationContext
from src.models.request import GenerateRequest
from src.models.response import GenerateResponse
from src.services.bandit.thompson import ThompsonBandit
from src.services.cat_model.client import CatModelClient
from src.services.firestore.client import FirestoreClient
from src.services.gemini.client import GeminiClient
from src.services.state_key.builder import StateKeyBuilder
from src.services.veo.client import VeoClient
from src.services.veo.signed_url import SignedUrlGenerator


class GenerateOrchestrator:
    """Coordinate the full /generate workflow."""

    def __init__(
        self: Self,
        settings: Settings,
        *,
        firestore_client: FirestoreClient | None = None,
        cat_model_client: CatModelClient | None = None,
        state_key_builder: StateKeyBuilder | None = None,
        bandit: ThompsonBandit | None = None,
        gemini_client: GeminiClient | None = None,
        veo_client: VeoClient | None = None,
        signed_url_generator: SignedUrlGenerator | None = None,
    ) -> None:
        self._settings = settings
        self._firestore = firestore_client or FirestoreClient(settings=settings)
        self._cat_model = cat_model_client or CatModelClient(settings=settings)
        self._state_key_builder = state_key_builder or StateKeyBuilder()
        self._bandit = bandit or ThompsonBandit(settings=settings, firestore_client=self._firestore)
        self._gemini = gemini_client or GeminiClient(settings=settings)
        self._veo = veo_client or VeoClient(settings=settings)
        self._signed_url_generator = signed_url_generator or SignedUrlGenerator(settings=settings)

    async def execute(self: Self, request: GenerateRequest) -> GenerateResponse:
        ctx = GenerationContext(
            session_id=str(uuid.uuid4()),
            mode=request.mode,
            image_base64=request.image_base64,
            audio_base64=request.audio_base64,
            user_context=request.user_context,
        )

        try:
            await self._firestore.create_session(ctx=ctx)
            templates = await self._firestore.get_active_templates()
            candidate_video_ids = [template.template_id for template in templates]
            ctx.cat_features = await self._cat_model.predict(
                image_base64=ctx.image_base64,
                audio_base64=ctx.audio_base64,
                candidate_video_ids=candidate_video_ids,
            )
            ctx.state_key = self._state_key_builder.build(features=ctx.cat_features)
            ctx.bandit_selection = await self._bandit.select(
                state_key=ctx.state_key,
                predicted_rewards=ctx.cat_features.predicted_rewards,
            )
            ctx.generated_prompt = await self._gemini.generate_prompt(
                template_text=ctx.bandit_selection.prompt_text,
                cat_features=ctx.cat_features,
                state_key=ctx.state_key,
                user_context=ctx.user_context,
            )
            ctx.video_gcs_uri = await self._veo.generate(prompt=ctx.generated_prompt)
            ctx.video_signed_url = self._signed_url_generator.generate(gcs_uri=ctx.video_gcs_uri)
            await self._firestore.mark_session_generated(ctx=ctx)
        except (
            FirestoreError,
            GeminiError,
            ModelServiceError,
            ModelServiceTimeoutError,
            TemplateSelectionError,
            VeoGenerationError,
            VeoTimeoutError,
        ) as exc:
            await self._safely_fail_session(ctx=ctx, exc=exc)
            raise

        return GenerateResponse(
            session_id=ctx.session_id,
            video_url=ctx.video_signed_url or "",
            state_key=ctx.state_key or "",
            template_id=ctx.bandit_selection.template_id if ctx.bandit_selection else "",
            template_name=ctx.bandit_selection.template_name if ctx.bandit_selection else "",
        )

    async def _safely_fail_session(
        self: Self,
        ctx: GenerationContext,
        exc: NekkoflixBaseError,
    ) -> None:
        try:
            await self._firestore.fail_session(ctx=ctx, error_msg=exc.detail or str(exc))
        except FirestoreError:
            pass
