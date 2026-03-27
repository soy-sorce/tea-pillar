"""Unit tests for backend rate-limiter primitives."""

from __future__ import annotations

from src.exceptions import RateLimitExceededError
from src.services.rate_limit.policies import WindowLimit
from src.services.rate_limit.service import InMemoryRateLimiter


def test_window_limit_rejects_request_after_threshold() -> None:
    now = 0.0
    limiter = InMemoryRateLimiter(now=lambda: now)
    limit = WindowLimit(name="test", requests=2, window_seconds=60)

    limiter.check_window(scope="generate", key="client-1", limit=limit)
    limiter.check_window(scope="generate", key="client-1", limit=limit)

    try:
        limiter.check_window(scope="generate", key="client-1", limit=limit)
    except RateLimitExceededError as exc:
        assert exc.status_code == 429
    else:
        raise AssertionError("expected RateLimitExceededError")


def test_window_limit_allows_request_after_window_passes() -> None:
    now_values = iter([0.0, 1.0, 61.0])
    limiter = InMemoryRateLimiter(now=lambda: next(now_values))
    limit = WindowLimit(name="test", requests=2, window_seconds=60)

    limiter.check_window(scope="generate", key="client-1", limit=limit)
    limiter.check_window(scope="generate", key="client-1", limit=limit)
    limiter.check_window(scope="generate", key="client-1", limit=limit)


def test_concurrency_limit_rejects_when_slots_are_exhausted() -> None:
    limiter = InMemoryRateLimiter(now=lambda: 0.0)
    lease = limiter.acquire_concurrency(scope="generate", key="client-1", limit=1)

    try:
        limiter.acquire_concurrency(scope="generate", key="client-1", limit=1)
    except RateLimitExceededError as exc:
        assert exc.status_code == 429
    else:
        raise AssertionError("expected RateLimitExceededError")
    finally:
        lease.release()
