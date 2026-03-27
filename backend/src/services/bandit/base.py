"""Bandit base interface."""

from abc import ABC, abstractmethod
from typing import Self

from src.models.firestore import TemplateDocument
from src.models.internal import BanditSelection


class BanditBase(ABC):
    """Abstract interface for template selection algorithms."""

    @abstractmethod
    async def select(
        self: Self,
        state_key: str,
        predicted_rewards: dict[str, float],
        templates: list[TemplateDocument] | None = None,
    ) -> BanditSelection:
        """Select a template for the given state."""

    @abstractmethod
    async def update(
        self: Self,
        template_id: str,
        state_key: str,
        reward: float,
    ) -> None:
        """Update the arm posterior for the given state and reward."""
