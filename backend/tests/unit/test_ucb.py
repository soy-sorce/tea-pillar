"""Unit tests for the UCB bandit implementation."""

from __future__ import annotations

import math
from typing import Self

import pytest
from src.exceptions import TemplateSelectionError
from src.models.firestore import BanditTableDocument, TemplateDocument
from src.services.bandit.ucb import UCBBandit


class FakeFirestoreClient:
    """In-memory Firestore substitute for UCB tests."""

    def __init__(
        self: Self,
        *,
        entries: dict[str, BanditTableDocument],
        templates: list[TemplateDocument],
    ) -> None:
        self.entries = entries
        self.templates = templates
        self.updated: tuple[str, str, float] | None = None

    async def get_bandit_entries_by_state_key(
        self: Self,
        state_key: str,
    ) -> dict[str, BanditTableDocument]:
        return {
            template_id: entry
            for template_id, entry in self.entries.items()
            if entry.state_key == state_key
        }

    async def get_active_templates(self: Self) -> list[TemplateDocument]:
        return self.templates

    async def update_bandit_entry(
        self: Self,
        template_id: str,
        state_key: str,
        reward: float,
    ) -> None:
        self.updated = (template_id, state_key, reward)


def _build_template(template_id: str, name: str) -> TemplateDocument:
    return TemplateDocument(
        template_id=template_id,
        name=name,
        prompt_text=f"prompt-{template_id}",
        is_active=True,
        auto_generated=False,
    )


async def test_select_chooses_highest_final_score() -> None:
    state_key = "unknown_happy_curious_cat"
    templates = [
        _build_template("video-1", "first"),
        _build_template("video-2", "second"),
    ]
    entries = {
        "video-1": BanditTableDocument(
            template_id="video-1",
            state_key=state_key,
            selection_count=10,
            cumulative_reward=5.0,
            mean_reward=0.5,
        ),
        "video-2": BanditTableDocument(
            template_id="video-2",
            state_key=state_key,
            selection_count=1,
            cumulative_reward=0.1,
            mean_reward=0.1,
        ),
    }
    firestore = FakeFirestoreClient(entries=entries, templates=templates)
    from src.config import Settings

    bandit = UCBBandit(settings=Settings(), firestore_client=firestore)  # type: ignore[arg-type]

    selection = await bandit.select(
        state_key=state_key,
        predicted_rewards={"video-1": 0.2, "video-2": 0.4},
    )

    assert selection.template_id == "video-2"
    assert selection.template_name == "second"
    assert selection.final_score > selection.predicted_reward


async def test_update_delegates_to_repository() -> None:
    templates = [_build_template("video-1", "first")]
    firestore = FakeFirestoreClient(entries={}, templates=templates)
    from src.config import Settings

    bandit = UCBBandit(settings=Settings(), firestore_client=firestore)  # type: ignore[arg-type]
    await bandit.update(
        template_id="video-1",
        state_key="unknown_sad_sleepy_cat",
        reward=1.0,
    )

    assert firestore.updated == ("video-1", "unknown_sad_sleepy_cat", 1.0)


async def test_select_raises_when_no_active_templates() -> None:
    from src.config import Settings

    bandit = UCBBandit(
        settings=Settings(),
        firestore_client=FakeFirestoreClient(entries={}, templates=[]),  # type: ignore[arg-type]
    )

    with pytest.raises(TemplateSelectionError):
        await bandit.select(
            state_key="unknown_happy_curious_cat",
            predicted_rewards={"video-1": 0.1},
        )


async def test_select_raises_when_predicted_reward_is_missing() -> None:
    from src.config import Settings

    bandit = UCBBandit(
        settings=Settings(),
        firestore_client=FakeFirestoreClient(
            entries={},
            templates=[_build_template("video-1", "first")],
        ),  # type: ignore[arg-type]
    )

    with pytest.raises(TemplateSelectionError):
        await bandit.select(
            state_key="unknown_happy_curious_cat",
            predicted_rewards={},
        )


def test_calculate_ucb_bonus_respects_alpha_and_count() -> None:
    from src.config import Settings

    bandit = UCBBandit(
        settings=Settings(bandit_ucb_alpha=2.0),
        firestore_client=FakeFirestoreClient(entries={}, templates=[]),  # type: ignore[arg-type]
    )

    assert bandit._calculate_ucb_bonus(total_n=0, selection_count=1) == 0.0
    assert math.isclose(
        bandit._calculate_ucb_bonus(total_n=10, selection_count=1),
        2.0 * math.sqrt(2 * math.log(10)),
    )
    assert bandit._calculate_ucb_bonus(
        total_n=10, selection_count=10
    ) < bandit._calculate_ucb_bonus(total_n=10, selection_count=1)
