"""In-memory rate-limit primitives."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from threading import Lock
from typing import Self

from fastapi import Request

from src.exceptions import RateLimitExceededError

from .policies import WindowLimit

NowFn = Callable[[], float]


class ConcurrencyLease:
    """Handle for a held concurrency slot."""

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
        """Release the held slot exactly once."""
        if self._released:
            return
        with self._lock:
            current = self._counters.get(self._storage_key, 0)
            if current <= 1:
                self._counters.pop(self._storage_key, None)
            else:
                self._counters[self._storage_key] = current - 1
        self._released = True


class InMemoryRateLimiter:
    """Thread-safe in-memory limiter for single-process app instances."""

    def __init__(self: Self, now: NowFn) -> None:
        self._now = now
        self._window_entries: dict[str, deque[float]] = {}
        self._concurrency_entries: dict[str, int] = {}
        self._lock = Lock()

    def reset(self: Self) -> None:
        """Clear all limiter state."""
        with self._lock:
            self._window_entries.clear()
            self._concurrency_entries.clear()

    def check_window(self: Self, *, scope: str, key: str, limit: WindowLimit) -> None:
        """Consume a single request from a fixed window or raise 429."""
        storage_key = f"{scope}:{limit.name}:{key}"
        now = self._now()
        threshold = now - float(limit.window_seconds)

        with self._lock:
            entries = self._window_entries.setdefault(storage_key, deque())
            while entries and entries[0] <= threshold:
                entries.popleft()
            if len(entries) >= limit.requests:
                raise RateLimitExceededError(
                    message="アクセスが集中しています。時間を置いて再試行してください",
                    detail=f"scope={scope} key={key} policy={limit.name}",
                )
            entries.append(now)

    def acquire_concurrency(
        self: Self,
        *,
        scope: str,
        key: str,
        limit: int,
    ) -> ConcurrencyLease:
        """Acquire a concurrency slot or raise 429."""
        storage_key = f"{scope}:concurrency:{key}"
        with self._lock:
            current = self._concurrency_entries.get(storage_key, 0)
            if current >= limit:
                raise RateLimitExceededError(
                    message="同時リクエスト数の上限に達しました。少し待って再試行してください",
                    detail=f"scope={scope} key={key} limit={limit}",
                )
            self._concurrency_entries[storage_key] = current + 1
        return ConcurrencyLease(
            counters=self._concurrency_entries,
            storage_key=storage_key,
            lock=self._lock,
        )


def extract_client_key(request: Request) -> str:
    """Build a stable-ish client key from forwarded headers or the socket peer."""
    forwarded_for = request.headers.get("x-forwarded-for", "").strip()
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client is not None and request.client.host:
        return request.client.host
    return "unknown"
