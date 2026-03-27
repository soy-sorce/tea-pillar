"""Thompson Sampling implementation."""

from __future__ import annotations

import random
from typing import Self

from src.config import Settings
from src.exceptions import TemplateSelectionError
from src.models.firestore import TemplateDocument
from src.models.internal import BanditSelection
from src.repositories.firestore import FirestoreClient
from src.services.bandit.base import BanditBase
from src.services.bandit.repository import BanditRepository


class ThompsonBandit(BanditBase):
    """Select templates by Thompson Sampling over Firestore bandit state."""

    def __init__(
        self: Self,
        settings: Settings,
        firestore_client: FirestoreClient,
    ) -> None:
        self._settings = settings
        self._repo = BanditRepository(firestore_client=firestore_client)

    async def select(
        self: Self,
        state_key: str,
        predicted_rewards: dict[str, float],
        templates: list[TemplateDocument] | None = None,
    ) -> BanditSelection:
        active_templates = templates or await self._repo.get_active_templates()
        if not active_templates:
            raise TemplateSelectionError(
                message="有効なテンプレートが存在しません",
                detail="templates collection is empty",
            )

        entries = await self._repo.get_entries_by_state_key(state_key=state_key)

        best: BanditSelection | None = None
        for template in active_templates:
            entry = entries.get(template.template_id)
            alpha = entry.alpha if entry is not None else self._settings.thompson_default_alpha
            beta = entry.beta if entry is not None else self._settings.thompson_default_beta
            predicted_reward = predicted_rewards.get(template.template_id, 0.0)
            bandit_score = random.betavariate(alpha, beta)
            final_score = predicted_reward + bandit_score
            current = BanditSelection(
                template_id=template.template_id,
                template_name=template.name,
                prompt_text=template.prompt_text,
                predicted_reward=predicted_reward,
                alpha=alpha,
                beta=beta,
                bandit_score=bandit_score,
                final_score=final_score,
            )
            if best is None or current.final_score > best.final_score:
                best = current

        assert best is not None
        return best

    async def update(self: Self, template_id: str, state_key: str, reward: float) -> None:
        await self._repo.update_entry(
            template_id=template_id,
            state_key=state_key,
            reward=reward,
        )
