"""Repository for bandit-related Firestore access."""

from src.models.firestore import BanditTableDocument, TemplateDocument
from src.services.firestore.client import FirestoreClient


class BanditRepository:
    """Hide Firestore details from the UCB implementation."""

    def __init__(self, firestore_client: FirestoreClient) -> None:
        self._firestore = firestore_client

    async def get_entries_by_state_key(
        self,
        state_key: str,
    ) -> dict[str, BanditTableDocument]:
        return await self._firestore.get_bandit_entries_by_state_key(state_key=state_key)

    async def get_active_templates(self) -> list[TemplateDocument]:
        return await self._firestore.get_active_templates()

    async def update_entry(
        self,
        template_id: str,
        state_key: str,
        reward: float,
    ) -> None:
        await self._firestore.update_bandit_entry(
            template_id=template_id,
            state_key=state_key,
            reward=reward,
        )
