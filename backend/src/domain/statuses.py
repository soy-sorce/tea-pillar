"""Shared domain status enums."""

from enum import StrEnum


class SessionMode(StrEnum):
    """Supported generation modes."""

    EXPERIENCE = "experience"
    PRODUCTION = "production"


class SessionStatus(StrEnum):
    """Session lifecycle states."""

    GENERATING = "generating"
    GENERATED = "generated"
    COMPLETED = "completed"
    FAILED = "failed"


class RewardStatus(StrEnum):
    """Reward analysis lifecycle states."""

    NOT_STARTED = "not_started"
    PENDING = "pending"
    DONE = "done"
    FAILED = "failed"
