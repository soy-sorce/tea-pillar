"""Bandit base interface."""

from abc import ABC, abstractmethod

from src.models.internal import BanditSelection


class BanditBase(ABC):
    """Abstract interface for template selection algorithms."""

    @abstractmethod
    async def select(
        self,
        state_key: str,
        predicted_rewards: dict[str, float],
    ) -> BanditSelection:
        """Select a template."""

    @abstractmethod
    async def update(
        self,
        template_id: str,
        state_key: str,
        reward: float,
    ) -> None:
        """Update the post-feedback statistics."""
