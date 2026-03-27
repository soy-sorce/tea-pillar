"""FastAPI dependencies for backend rate limiting."""

from __future__ import annotations

import time
from collections.abc import AsyncIterator

from fastapi import Request

from . import policies
from .service import InMemoryRateLimiter, extract_client_key

_LIMITER = InMemoryRateLimiter(now=time.monotonic)


def reset_rate_limit_state() -> None:
    """Reset singleton limiter state for tests."""
    _LIMITER.reset()


def get_rate_limiter() -> InMemoryRateLimiter:
    """Return the backend limiter singleton."""
    return _LIMITER


async def enforce_health_limit(request: Request) -> None:
    """Apply a relaxed health-check limit per client."""
    limiter = get_rate_limiter()
    limiter.check_window(
        scope="health",
        key=extract_client_key(request),
        limit=policies.HEALTH_LIMIT,
    )


async def enforce_generate_limits(request: Request) -> AsyncIterator[None]:
    """Apply generate route limits and hold a concurrency slot."""
    limiter = get_rate_limiter()
    client_key = extract_client_key(request)
    for window_limit in policies.GENERATE_WINDOW_LIMITS:
        limiter.check_window(scope="generate", key=client_key, limit=window_limit)
    lease = limiter.acquire_concurrency(
        scope="generate",
        key=client_key,
        limit=policies.GENERATE_CONCURRENCY_LIMIT,
    )
    try:
        yield
    finally:
        lease.release()


async def enforce_reaction_upload_limits(session_id: str, request: Request) -> None:
    """Apply upload-url limits by client and session."""
    limiter = get_rate_limiter()
    limiter.check_window(
        scope="reaction-upload-client",
        key=extract_client_key(request),
        limit=policies.REACTION_UPLOAD_CLIENT_LIMIT,
    )
    limiter.check_window(
        scope="reaction-upload-session",
        key=session_id,
        limit=policies.REACTION_UPLOAD_SESSION_LIMIT,
    )


async def enforce_reaction_complete_limits(session_id: str, request: Request) -> None:
    """Apply reaction completion limits by client and session."""
    limiter = get_rate_limiter()
    limiter.check_window(
        scope="reaction-complete-client",
        key=extract_client_key(request),
        limit=policies.REACTION_COMPLETE_CLIENT_LIMIT,
    )
    limiter.check_window(
        scope="reaction-complete-session",
        key=session_id,
        limit=policies.REACTION_COMPLETE_SESSION_LIMIT,
    )
