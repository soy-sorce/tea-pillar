"""Unit tests for the hybrid Thompson selector."""

from __future__ import annotations

from src.config import Settings
from src.models.firestore import BanditStateDocument, TemplateDocument
from src.services.bandit.thompson import ThompsonBandit


class FakeFirestoreClient:
    async def get_active_templates(self) -> list[TemplateDocument]:
        return [
            TemplateDocument(
                template_id="video-1",
                name="template-1",
                prompt_text="prompt-1",
                is_active=True,
            ),
            TemplateDocument(
                template_id="video-2",
                name="template-2",
                prompt_text="prompt-2",
                is_active=True,
            ),
        ]

    async def get_bandit_states_by_state_key(
        self,
        state_key: str,
    ) -> dict[str, BanditStateDocument]:
        del state_key
        return {
            "video-1": BanditStateDocument(
                template_id="video-1",
                state_key="state",
                alpha=1.0,
                beta=1.0,
            ),
            "video-2": BanditStateDocument(
                template_id="video-2",
                state_key="state",
                alpha=1.0,
                beta=1.0,
            ),
        }

    async def update_bandit_state(self, *, template_id: str, state_key: str, reward: float) -> None:
        del template_id, state_key, reward


async def test_select_prefers_best_combined_score(monkeypatch) -> None:
    sequence = iter([0.1, 0.2])
    monkeypatch.setattr(
        "src.services.bandit.thompson.random.betavariate",
        lambda a, b: next(sequence),
    )

    bandit = ThompsonBandit(
        settings=Settings(),
        firestore_client=FakeFirestoreClient(),  # type: ignore[arg-type]
    )

    selection = await bandit.select(
        state_key="unknown_happy_curious_cat",
        predicted_rewards={"video-1": 0.9, "video-2": 0.1},
    )

    assert selection.template_id == "video-1"
    assert selection.predicted_reward == 0.9
    assert selection.bandit_score == 0.1
    assert selection.final_score == 1.0
