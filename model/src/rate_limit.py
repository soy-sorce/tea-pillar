"""In-memory rate limiting for model endpoints."""

from __future__ import annotations

import time
from collections import deque
from collections.abc import AsyncIterator
from dataclasses import dataclass
from threading import Lock
from typing import Self

from fastapi import HTTPException


@dataclass(frozen=True, slots=True)
class WindowLimit:
    """Fixed-window rate policy."""

    requests: int
    window_seconds: int


PREDICT_RATE_LIMIT = WindowLimit(requests=120, window_seconds=60)
PREDICT_CONCURRENCY_LIMIT = 8
ANALYZE_REWARD_RATE_LIMIT = WindowLimit(requests=30, window_seconds=60)
ANALYZE_REWARD_CONCURRENCY_LIMIT = 3


class _ConcurrencyLease:
    def __init__(
        self: Self,
        *,
        counters: dict[str, int],
        storage_key: str,
        lock: Lock,
    ) -> None:
        self._counters = counters
        self._storage_key = storage_key
        self._lock = lock
        self._released = False

    def release(self: Self) -> None:
        if self._released:
            return
        with self._lock:
            current = self._counters.get(self._storage_key, 0)
            if current <= 1:
                self._counters.pop(self._storage_key, None)
            else:
                self._counters[self._storage_key] = current - 1
        self._released = True


class _InMemoryLimiter:
    def __init__(self: Self) -> None:
        self._windows: dict[str, deque[float]] = {}
        self._concurrency: dict[str, int] = {}
        self._lock = Lock()

    def reset(self: Self) -> None:
        with self._lock:
            self._windows.clear()
            self._concurrency.clear()

    def check_window(self: Self, *, scope: str, limit: WindowLimit) -> None:
        now = time.monotonic()
        threshold = now - float(limit.window_seconds)
        with self._lock:
            entries = self._windows.setdefault(scope, deque())
            while entries and entries[0] <= threshold:
                entries.popleft()
            if len(entries) >= limit.requests:
                raise HTTPException(status_code=429, detail="rate limit exceeded")
            entries.append(now)

    def acquire_concurrency(self: Self, *, scope: str, limit: int) -> _ConcurrencyLease:
        with self._lock:
            current = self._concurrency.get(scope, 0)
            if current >= limit:
                raise HTTPException(status_code=429, detail="concurrency limit exceeded")
            self._concurrency[scope] = current + 1
        return _ConcurrencyLease(counters=self._concurrency, storage_key=scope, lock=self._lock)


_LIMITER = _InMemoryLimiter()


def reset_rate_limit_state() -> None:
    """Reset limiter state for tests."""
    _LIMITER.reset()


async def enforce_predict_limits() -> AsyncIterator[None]:
    """Apply predict endpoint limits."""
    _LIMITER.check_window(scope="predict", limit=PREDICT_RATE_LIMIT)
    lease = _LIMITER.acquire_concurrency(
        scope="predict",
        limit=PREDICT_CONCURRENCY_LIMIT,
    )
    try:
        yield
    finally:
        lease.release()


async def enforce_analyze_reward_limits() -> AsyncIterator[None]:
    """Apply analyze-reward endpoint limits."""
    _LIMITER.check_window(scope="analyze-reward", limit=ANALYZE_REWARD_RATE_LIMIT)
    lease = _LIMITER.acquire_concurrency(
        scope="analyze-reward",
        limit=ANALYZE_REWARD_CONCURRENCY_LIMIT,
    )
    try:
        yield
    finally:
        lease.release()
