"""Gemini client."""

import asyncio

import structlog
import vertexai
from google.api_core.exceptions import DeadlineExceeded, GoogleAPICallError, RetryError
from vertexai.generative_models import GenerativeModel

from src.config import Settings
from src.exceptions import GeminiError, NotConfiguredError
from src.models.internal import CatFeatures
from src.services.gemini.prompt_builder import PromptBuilder

logger = structlog.get_logger(__name__)


class GeminiClient:
    """Generate the final Veo prompt from the selected template."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._prompt_builder = PromptBuilder()

    async def generate_prompt(
        self,
        template_text: str,
        cat_features: CatFeatures,
        state_key: str,
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

        vertexai.init(
            project=self._settings.gcp_project_id,
            location=self._settings.gcp_region,
        )
        model = GenerativeModel(self._settings.gemini_model)

        try:
            response = await asyncio.wait_for(
                model.generate_content_async(
                    prompt,
                    generation_config={"max_output_tokens": 512, "temperature": 0.7},
                ),
                timeout=self._settings.gemini_timeout,
            )
        except TimeoutError as exc:
            raise GeminiError(
                message="Gemini の応答がタイムアウトしました",
                detail=str(exc),
            ) from exc
        except DeadlineExceeded as exc:
            raise GeminiError(
                message="Gemini の応答がタイムアウトしました",
                detail=str(exc),
            ) from exc
        except RetryError as exc:
            raise GeminiError(
                message="Gemini の応答がタイムアウトしました",
                detail=str(exc),
            ) from exc
        except GoogleAPICallError as exc:
            raise GeminiError(detail=str(exc)) from exc

        generated_text = response.text.strip()
        logger.info(
            "gemini_prompt_generated",
            state_key=state_key,
            output_prompt_length=len(generated_text),
        )
        return generated_text
