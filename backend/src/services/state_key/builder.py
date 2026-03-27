"""State key generation."""

from typing import Self

import structlog
from src.models.internal import CatFeatures

logger = structlog.get_logger(__name__)


class StateKeyBuilder:
    """Build the state key from endpoint auxiliary labels."""

    def build(self: Self, features: CatFeatures) -> str:
        """Build the v1 state key.

        Format:
            "{meow_label or unknown}_{emotion_label}_{clip_top_label}"
        """
        meow_part = features.meow_label or "unknown"
        state_key = f"{meow_part}_{features.emotion_label}_{features.clip_top_label}"
        logger.debug(
            "state_key_built",
            state_key=state_key,
            meow_fallback_used=features.meow_label is None,
        )
        return state_key
