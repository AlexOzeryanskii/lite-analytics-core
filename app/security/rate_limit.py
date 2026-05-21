"""In-memory IP-based rate limiting for public endpoints."""

from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock

from fastapi import HTTPException, Request, status

from app.deps import get_client_ip
from app.logger import get_logger

logger = get_logger(__name__)

RATE_LIMIT_DETAIL = "Rate limit exceeded"


class InMemoryRateLimiter:
    """Fixed-window counter stored in process memory."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._windows: dict[str, tuple[int, float]] = {}
        self._lock = Lock()

    def is_allowed(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            count, window_start = self._windows.get(key, (0, now))
            if now - window_start >= self.window_seconds:
                count = 0
                window_start = now
            if count >= self.max_requests:
                self._windows[key] = (count, window_start)
                return False
            self._windows[key] = (count + 1, window_start)
            return True

    def prune(self, max_entries: int = 10_000) -> None:
        if len(self._windows) <= max_entries:
            return
        now = time.monotonic()
        with self._lock:
            expired = [
                k
                for k, (_, start) in self._windows.items()
                if now - start >= self.window_seconds
            ]
            for k in expired:
                self._windows.pop(k, None)


track_limiter = InMemoryRateLimiter(max_requests=120, window_seconds=60)
push_subscribe_limiter = InMemoryRateLimiter(max_requests=20, window_seconds=3600)


def _client_key(request: Request) -> str:
    return get_client_ip(request) or "unknown"


def enforce_track_rate_limit(request: Request) -> None:
    key = _client_key(request)
    if track_limiter.is_allowed(key):
        return
    logger.warning("Rate limit exceeded for /api/track from %s", key)
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=RATE_LIMIT_DETAIL,
    )


def enforce_push_subscribe_rate_limit(request: Request) -> None:
    key = _client_key(request)
    if push_subscribe_limiter.is_allowed(key):
        return
    logger.warning("Rate limit exceeded for /api/push/subscribe from %s", key)
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=RATE_LIMIT_DETAIL,
    )
