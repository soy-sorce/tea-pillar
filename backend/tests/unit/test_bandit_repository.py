"""Unit tests for the bandit repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from src.models.firestore import BanditTableDocument, TemplateDocument
from src.services.bandit.repository import BanditRepository


@dataclass
class FakeFirestoreClient:
    entries: dict[str, BanditTableDocument]
    templates: list[TemplateDocument]
    updated: tuple[str, str, float] | None = None

    async def get_bandit_entries_by_state_key(
        self: Self,
        state_key: str,
    ) -> dict[str, BanditTableDocument]:
        return {
            template_id: document
            for template_id, document in self.entries.items()
            if document.state_key == state_key
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


async def test_repository_delegates_reads_and_writes() -> None:
    firestore = FakeFirestoreClient(
        entries={
            "video-1": BanditTableDocument(
                template_id="video-1",
                state_key="unknown_happy_curious_cat",
                selection_count=2,
                cumulative_reward=1.0,
                mean_reward=0.5,
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
