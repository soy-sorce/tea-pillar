"""State key generation."""

from src.models.internal import CatFeatures


class StateKeyBuilder:
    """Build the state key from endpoint auxiliary labels."""

    def build(self, features: CatFeatures) -> str:
        """Build the v1 state key.

        Format:
            "{meow_label or unknown}_{emotion_label}_{clip_top_label}"
        """
        meow_part = features.meow_label or "unknown"
        return f"{meow_part}_{features.emotion_label}_{features.clip_top_label}"
