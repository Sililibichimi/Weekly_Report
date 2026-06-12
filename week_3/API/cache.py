from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from time import monotonic
from typing import Any, Hashable


@dataclass
class CacheStats:
    name: str
    size: int
    maxsize: int
    ttl_seconds: int


class TTLMemoryCache:
    """Small thread-safe TTL cache for local/demo API serving."""

    def __init__(self, name: str, maxsize: int, ttl_seconds: int) -> None:
        self.name = name
        self.maxsize = maxsize
        self.ttl_seconds = ttl_seconds
        self._items: dict[Hashable, tuple[float, Any]] = {}
        self._lock = RLock()

    def get(self, key: Hashable) -> Any | None:
        now = monotonic()
        with self._lock:
            item = self._items.get(key)
            if item is None:
                return None

            expires_at, value = item
            if expires_at <= now:
                self._items.pop(key, None)
                return None
            return value

    def set(self, key: Hashable, value: Any) -> None:
        expires_at = monotonic() + self.ttl_seconds
        with self._lock:
            if len(self._items) >= self.maxsize:
                self._evict_one()
            self._items[key] = (expires_at, value)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()

    def stats(self) -> CacheStats:
        self._drop_expired()
        with self._lock:
            return CacheStats(
                name=self.name,
                size=len(self._items),
                maxsize=self.maxsize,
                ttl_seconds=self.ttl_seconds,
            )

    def _drop_expired(self) -> None:
        now = monotonic()
        with self._lock:
            expired_keys = [
                key for key, (expires_at, _) in self._items.items() if expires_at <= now
            ]
            for key in expired_keys:
                self._items.pop(key, None)

    def _evict_one(self) -> None:
        if not self._items:
            return
        oldest_key = min(self._items, key=lambda key: self._items[key][0])
        self._items.pop(oldest_key, None)


class CacheManager:
    def __init__(
        self,
        feature_maxsize: int,
        feature_ttl_seconds: int,
        prediction_maxsize: int,
        prediction_ttl_seconds: int,
    ) -> None:
        self.feature_cache = TTLMemoryCache(
            name="feature_lookup",
            maxsize=feature_maxsize,
            ttl_seconds=feature_ttl_seconds,
        )
        self.prediction_cache = TTLMemoryCache(
            name="prediction",
            maxsize=prediction_maxsize,
            ttl_seconds=prediction_ttl_seconds,
        )

    def status(self) -> dict[str, dict[str, int | str]]:
        return {
            "feature_cache": self.feature_cache.stats().__dict__,
            "prediction_cache": self.prediction_cache.stats().__dict__,
        }

    def clear(self) -> None:
        self.feature_cache.clear()
        self.prediction_cache.clear()

