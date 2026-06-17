from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from time import monotonic
from typing import Any, Hashable

import json

import redis

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

class RedisCache:
    """Cache backend dùng Redis - cùng interface với TTLMemoryCache

    Mỗi cache có một `name` làm namespace để làm feature cache và 
    prediction cache không đụng nhau trong cùng một redis.
    """
    def __init__(self, client: "redis.Redis", name: str, ttl_seconds: int) -> None:
            self.client = client
            self.name = name
            self.ttl_seconds = ttl_seconds 
    
    def _full_key(self, key: Hashable) -> str:
        # Tuple key -> chuỗi ổn định. default = str để int/bool cũng serialize được
        return f"{self.name}:" + json.dumps(key, default=str)
    
    def get(self, key: Hashable) -> Any | None :
        raw = self.client.get(self._full_key(key))
        if raw is None:
            return None
        return json.load(raw)
    
    def set(self, key: Hashable, value: Any) -> None:
        self.client.setex(self._full_key(key), self.ttl_seconds, json.dumps(value, default=str))

    def clear(self) -> None:
        # Chỉ xóa key thuộc namespace này (không đụng cache khác). SCAN thay vì keys để không block Redis
        keys = list(self.client.scan_iter(match=f"{self.name}", count=500))
        if keys:
            self.client.delete(*keys)

    def stats(self) -> CacheStats:
        size = sum(1 for _ in self.client.scan_iter(match=f"{self.name}", count = 500))
        #  maxsize = -1: Redis không evict thủ công như bản memory; dựa vào TTL.
        return CacheStats(name=self.name, size=size, maxsize=-1, ttl_seconds=self.ttl_seconds)
    
class CacheManager:
    def __init__(
        self,
        feature_maxsize: int,
        feature_ttl_seconds: int,
        prediction_maxsize: int,
        prediction_ttl_seconds: int,
        backend: str = "memory",
        redis_url: str | None = None,
    ) -> None:
        
        self.backend = backend
        if backend == "redis" :
            client = redis.from_url(redis_url, decode_responses=True)
            client.ping() # fail fast nếu redis không kết nối được thì báo lỗi ngay lúc khởi động
            self.feature_cache = RedisCache(client, "feature_lookup", feature_ttl_seconds)
            self.prediction_cache = RedisCache(client, "prediction", prediction_ttl_seconds)
        else:
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

    def  clear(self) -> None:
        self.feature_cache.clear()
        self.prediction_cache.clear()

