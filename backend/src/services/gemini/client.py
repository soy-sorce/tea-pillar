"""Gemini client."""

import asyncio
from typing import Self

import structlog
import vertexai
from google.api_core.exceptions import DeadlineExceeded, GoogleAPICallError, RetryError
from src.config import Settings
from src.exceptions import GeminiError, NotConfiguredError
from src.models.internal import CatFeatures
from src.services.gemini.prompt_builder import PromptBuilder
from vertexai.generative_models import GenerativeModel

logger = structlog.get_logger(__name__)


class GeminiClient:
    """Generate the final Veo prompt from the selected template."""

    def __init__(self: Self, settings: Settings) -> None:
        self._settings = settings
        self._prompt_builder = PromptBuilder()

    async def generate_prompt(
        self: Self,
        template_text: str,
        cat_features: CatFeatures | None,
        state_key: str | None,
        user_context: str | None,
    ) -> str:
        """Call Gemini and return only the prompt text."""
        if not self._settings.gcp_project_id:
            raise NotConfiguredError(
                message="Gemini の設定が未完了です",
                detail="gcp_project_id is empty",
            )

        prompt = self._prompt_builder.build(
            template_text=template_text,
            cat_features=cat_features,
            state_key=state_key,
            user_context=user_context,
        )
        logger.info(
            "gemini_prompt_generation_start",
            model=self._settings.gemini_model,
            state_key=state_key,
            has_user_context=user_context is not None,
            input_prompt_length=len(prompt),
        )
        logger.debug(
            "gemini_prompt_generation_detail",
            project_id=self._settings.gcp_project_id,
            location=self._settings.gcp_region,
            timeout_seconds=self._settings.gemini_timeout,
            template_length=len(template_text),
            prompt_preview=prompt[:500],
        )

        vertexai.init(
            project=self._settings.gcp_project_id,
            location=self._settings.gcp_region,
        )
        model = GenerativeModel(self._settings.gemini_model)

        try:
            response = await asyncio.wait_for(
                model.generate_content_async(
                    prompt,
                    generation_config={"max_output_tokens": 4096, "temperature": 0.7},
                ),
                timeout=self._settings.gemini_timeout,
            )
        except TimeoutError as exc:
            logger.exception(
                "gemini_timeout_error",
                model=self._settings.gemini_model,
                timeout_seconds=self._settings.gemini_timeout,
            )
            raise GeminiError(
                message="Gemini の応答がタイムアウトしました",
                detail=str(exc),
            ) from exc
        except DeadlineExceeded as exc:
            logger.exception(
                "gemini_deadline_exceeded",
                model=self._settings.gemini_model,
                timeout_seconds=self._settings.gemini_timeout,
            )
            raise GeminiError(
                message="Gemini の応答がタイムアウトしました",
                detail=str(exc),
            ) from exc
        except RetryError as exc:
            logger.exception(
                "gemini_retry_error",
                model=self._settings.gemini_model,
                timeout_seconds=self._settings.gemini_timeout,
            )
            raise GeminiError(
                message="Gemini の応答がタイムアウトしました",
                detail=str(exc),
            ) from exc
        except GoogleAPICallError as exc:
            logger.exception(
                "gemini_google_api_error",
                model=self._settings.gemini_model,
                project_id=self._settings.gcp_project_id,
                location=self._settings.gcp_region,
                error_type=type(exc).__name__,
            )
            raise GeminiError(detail=str(exc)) from exc

        generated_text = response.text.strip()
        logger.debug(
            "gemini_prompt_generated_detail",
            output_preview=generated_text[:500],
        )
        logger.info(
            "gemini_prompt_generated",
            state_key=state_key,
            output_prompt_length=len(generated_text),
        )
        return generated_text
