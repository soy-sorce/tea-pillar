"""Unit tests for the bandit repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from src.models.firestore import BanditStateDocument, TemplateDocument
from src.services.bandit.repository import BanditRepository


@dataclass
class FakeFirestoreClient:
    entries: dict[str, BanditStateDocument]
    templates: list[TemplateDocument]
    updated: tuple[str, str, float] | None = None

    async def get_bandit_states_by_state_key(
        self: Self,
        state_key: str,
    ) -> dict[str, BanditStateDocument]:
        return {
            template_id: document
            for template_id, document in self.entries.items()
            if document.state_key == state_key
        }

    async def get_active_templates(self: Self) -> list[TemplateDocument]:
        return self.templates

    async def update_bandit_state(
        self: Self,
        *,
        template_id: str,
        state_key: str,
        reward: float,
    ) -> None:
        self.updated = (template_id, state_key, reward)


async def test_repository_delegates_reads_and_writes() -> None:
    firestore = FakeFirestoreClient(
        entries={
            "video-1": BanditStateDocument(
                template_id="video-1",
                state_key="unknown_happy_curious_cat",
                alpha=2.0,
                beta=1.0,
                selection_count=2,
                reward_sum=1.0,
            ),
        },
        templates=[
            TemplateDocument(
                template_id="video-1",
                name="template",
                prompt_text="prompt",
                is_active=True,
                auto_generated=False,
            ),
        ],
    )
    repository = BanditRepository(firestore_client=firestore)  # type: ignore[arg-type]

    entries = await repository.get_entries_by_state_key("unknown_happy_curious_cat")
    templates = await repository.get_active_templates()
    await repository.update_entry("video-1", "unknown_happy_curious_cat", 1.0)

    assert list(entries) == ["video-1"]
    assert templates[0].template_id == "video-1"
    assert firestore.updated == ("video-1", "unknown_happy_curious_cat", 1.0)
