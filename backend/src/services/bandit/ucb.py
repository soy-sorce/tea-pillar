"""UCB1 implementation."""

import math

import structlog

from src.config import Settings
from src.exceptions import TemplateSelectionError
from src.models.internal import BanditSelection
from src.services.bandit.base import BanditBase
from src.services.bandit.repository import BanditRepository
from src.services.firestore.client import FirestoreClient

logger = structlog.get_logger(__name__)


class UCBBandit(BanditBase):
    """Select templates by predicted reward + UCB bonus."""

    def __init__(self, settings: Settings, firestore_client: FirestoreClient) -> None:
        self._alpha = settings.bandit_ucb_alpha
        self._repo = BanditRepository(firestore_client=firestore_client)

    async def select(
        self,
        state_key: str,
        predicted_rewards: dict[str, float],
    ) -> BanditSelection:
        """Return the best active template for the given state."""
        table_entries = await self._repo.get_entries_by_state_key(state_key=state_key)
        templates = await self._repo.get_active_templates()

        if not templates:
            raise TemplateSelectionError(
                message="有効なテンプレートが存在しません",
                detail="templates collection is empty",
            )

        total_n = sum(entry.selection_count for entry in table_entries.values())
        log_total = math.log(max(total_n, 1))

        best_selection: BanditSelection | None = None
        for template in templates:
            if template.template_id not in predicted_rewards:
                raise TemplateSelectionError(
                    message="モデル出力とテンプレート定義が一致していません",
                    detail=f"missing_predicted_reward_for={template.template_id}",
                )

            entry = table_entries.get(template.template_id)
            selection_count = entry.selection_count if entry is not None else 1
            predicted_reward = predicted_rewards[template.template_id]
            ucb_bonus = self._calculate_ucb_bonus(
                total_n=total_n,
                selection_count=selection_count,
            )
            final_score = predicted_reward + ucb_bonus
            selection = BanditSelection(
                template_id=template.template_id,
                template_name=template.name,
                prompt_text=template.prompt_text,
                predicted_reward=predicted_reward,
                ucb_bonus=ucb_bonus,
                final_score=final_score,
            )
            if best_selection is None or selection.final_score > best_selection.final_score:
                best_selection = selection

        assert best_selection is not None
        logger.info(
            "bandit_selected",
            state_key=state_key,
            template_id=best_selection.template_id,
            predicted_reward=best_selection.predicted_reward,
            ucb_bonus=best_selection.ucb_bonus,
            final_score=best_selection.final_score,
            total_n=total_n,
            log_total=log_total,
        )
        return best_selection

    async def update(
        self,
        template_id: str,
        state_key: str,
        reward: float,
    ) -> None:
        """Update the chosen arm statistics."""
        await self._repo.update_entry(
            template_id=template_id,
            state_key=state_key,
            reward=reward,
        )

    def _calculate_ucb_bonus(self, total_n: int, selection_count: int) -> float:
        """Compute the UCB exploration bonus."""
        return self._alpha * math.sqrt(2 * math.log(max(total_n, 1)) / selection_count)
