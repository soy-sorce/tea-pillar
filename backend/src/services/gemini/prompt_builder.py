"""Gemini prompt builder."""

from typing import Self

from src.models.internal import CatFeatures

_NORMAL_SYSTEM_INSTRUCTION = """\
You create exactly one video prompt for a cat-focused video.
Use the template query, owner context, and constraints below.
Output exactly one prompt in English, with no heading, explanation, or multiple options."""

_NORMAL_CONSTRAINTS = """\
- silent video
- visually engaging motion that is likely to attract a cat's attention
- short-form concept around 10 to 15 seconds
- photorealistic tone that avoids creepy or unsettling imagery
- composition that makes it easy to guide the cat's gaze across the frame"""


class PromptBuilder:
    """Build the Gemini input prompt."""

    def build(
        self: Self,
        template_text: str,
        cat_features: CatFeatures | None,
        state_key: str | None,
        user_context: str | None,
    ) -> str:
        """Assemble the prompt from the template, owner context, and constraints."""
        del cat_features, state_key
        context_section = user_context if user_context else "none"
        return f"""{_NORMAL_SYSTEM_INSTRUCTION}

[Template Query]
{template_text}

[Owner Context]
{context_section}

[Constraints]
{_NORMAL_CONSTRAINTS}
"""
