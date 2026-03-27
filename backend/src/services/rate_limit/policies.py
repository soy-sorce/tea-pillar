"""Hard-coded backend rate-limit policies."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WindowLimit:
    """Fixed-window request limit."""

    name: str
    requests: int
    window_seconds: int


HEALTH_LIMIT = WindowLimit(name="health_per_minute", requests=180, window_seconds=60)

GENERATE_WINDOW_LIMITS = (
    WindowLimit(name="generate_per_minute", requests=20, window_seconds=60),
    WindowLimit(name="generate_per_hour", requests=100, window_seconds=3600),
)
GENERATE_CONCURRENCY_LIMIT = 3

REACTION_UPLOAD_CLIENT_LIMIT = WindowLimit(
    name="reaction_upload_per_minute",
    requests=60,
    window_seconds=60,
)
REACTION_UPLOAD_SESSION_LIMIT = WindowLimit(
    name="reaction_upload_per_session_minute",
    requests=10,
    window_seconds=60,
)

REACTION_COMPLETE_CLIENT_LIMIT = WindowLimit(
    name="reaction_complete_per_minute",
    requests=60,
    window_seconds=60,
)
REACTION_COMPLETE_SESSION_LIMIT = WindowLimit(
    name="reaction_complete_per_session_minute",
    requests=5,
    window_seconds=60,
)
