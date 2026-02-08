"""
MarketGPS Cache Layer
Redis-backed with in-memory LRU fallback.

Provides a unified caching interface that transparently handles both
Redis and in-memory caching. All operations gracefully degrade if
cache backend is unavailable - errors never break the application.
"""

import json
import logging
import time
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import Optional, Any, Dict, List
from functools import wraps
from datetime import datetime

logger = logging.getLogger(__name__)


class CacheBackend(ABC):
    """Abstract base class for cache implementations."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache. Returns None if key not found or expired."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL in seconds. Returns success status."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete key from cache. Returns success status."""
        pass

    @abstractmethod
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern (e.g., 'assets:*'). Returns count deleted."""
        pass

    @abstractmethod
    def clear(self) -> bool:
        """Clear entire cache. Returns success status."""
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics (hits, misses, size)."""
        pass


class MemoryCache(CacheBackend):
    """In-memory LRU cache with TTL support."""

    def __init__(self, max_entries: int = 10000):
        """
        Initialize in-memory cache.

        Args:
            max_entries: Maximum number of entries (default 10,000)
        """
        self.max_entries = max_entries
        self.data: OrderedDict = OrderedDict()  # key -> (value, expiry_time)
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache, checking TTL."""
        try:
            if key not in self.data:
                self.misses += 1
                return None

            value, expiry_time = self.data[key]

            # Check if expired
            if expiry_time is not None and time.time() > expiry_time:
                del self.data[key]
                self.misses += 1
                return None

            # Move to end (LRU)
            self.data.move_to_end(key)
            self.hits += 1

            # Deserialize from JSON
            return json.loads(value) if isinstance(value, str) else value
        except Exception as e:
            logger.warning(f"MemoryCache.get error for key '{key}': {e}")
            self.misses += 1
            return None

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL."""
        try:
            # Serialize to JSON
            serialized = json.dumps(value, default=str)

            # Calculate expiry
            expiry_time = time.time() + ttl if ttl > 0 else None

            # Check size limit
            if len(self.data) >= self.max_entries and key not in self.data:
                # Remove oldest item (first in OrderedDict)
                oldest_key = next(iter(self.data))
                del self.data[oldest_key]
                logger.debug(f"MemoryCache evicted oldest key: {oldest_key}")

            self.data[key] = (serialized, expiry_time)

            # Move to end (most recently used)
            self.data.move_to_end(key)

            return True
        except Exception as e:
            logger.warning(f"MemoryCache.set error for key '{key}': {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            if key in self.data:
                del self.data[key]
                return True
            return False
        except Exception as e:
            logger.warning(f"MemoryCache.delete error for key '{key}': {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern (e.g., 'assets:*')."""
        try:
            if "*" not in pattern:
                # Not a pattern, just delete single key
                return 1 if self.delete(pattern) else 0

            # Simple wildcard matching (prefix*)
            prefix = pattern.rstrip("*")
            keys_to_delete = [k for k in self.data.keys() if k.startswith(prefix)]

            for key in keys_to_delete:
                del self.data[key]

            return len(keys_to_delete)
        except Exception as e:
            logger.warning(f"MemoryCache.delete_pattern error for pattern '{pattern}': {e}")
            return 0

    def clear(self) -> bool:
        """Clear entire cache."""
        try:
            self.data.clear()
            self.hits = 0
            self.misses = 0
            return True
        except Exception as e:
            logger.warning(f"MemoryCache.clear error: {e}")
            return False

    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "size": len(self.data),
            "max_entries": self.max_entries,
            "hit_rate": (
                self.hits / (self.hits + self.misses)
                if (self.hits + self.misses) > 0
                else 0
            ),
        }


class RedisCache(CacheBackend):
    """Redis-backed cache implementation (async-compatible)."""

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize Redis cache.

        Args:
            redis_url: Redis connection URL (e.g., redis://localhost:6379)
        """
        import os
        import redis

        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.client = None
        self.hits = 0
        self.misses = 0

        try:
            # Parse connection URL
            self.client = redis.from_url(self.redis_url, decode_responses=True)

            # Test connection
            self.client.ping()
            logger.info(f"RedisCache connected to {self.redis_url}")
        except Exception as e:
            logger.warning(f"RedisCache initialization failed: {e}. Falling back to MemoryCache.")
            self.client = None

    def is_available(self) -> bool:
        """Check if Redis is available."""
        return self.client is not None

    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis."""
        if not self.is_available():
            self.misses += 1
            return None

        try:
            value = self.client.get(key)
            if value is None:
                self.misses += 1
                return None

            self.hits += 1
            return json.loads(value)
        except Exception as e:
            logger.warning(f"RedisCache.get error for key '{key}': {e}")
            self.misses += 1
            return None

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in Redis with TTL."""
        if not self.is_available():
            return False

        try:
            serialized = json.dumps(value, default=str)
            if ttl > 0:
                self.client.setex(key, ttl, serialized)
            else:
                self.client.set(key, serialized)
            return True
        except Exception as e:
            logger.warning(f"RedisCache.set error for key '{key}': {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        if not self.is_available():
            return False

        try:
            return self.client.delete(key) > 0
        except Exception as e:
            logger.warning(f"RedisCache.delete error for key '{key}': {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern using SCAN."""
        if not self.is_available():
            return 0

        try:
            cursor = 0
            deleted = 0

            while True:
                cursor, keys = self.client.scan(cursor, match=pattern, count=100)
                if keys:
                    deleted += self.client.delete(*keys)
                if cursor == 0:
                    break

            return deleted
        except Exception as e:
            logger.warning(f"RedisCache.delete_pattern error for pattern '{pattern}': {e}")
            return 0

    def clear(self) -> bool:
        """Clear entire Redis database."""
        if not self.is_available():
            return False

        try:
            self.client.flushdb()
            self.hits = 0
            self.misses = 0
            return True
        except Exception as e:
            logger.warning(f"RedisCache.clear error: {e}")
            return False

    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics from Redis INFO."""
        try:
            if not self.is_available():
                return {"error": "Redis unavailable"}

            info = self.client.info("stats")
            return {
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "size": self.client.dbsize(),
                "hit_rate": (
                    info.get("keyspace_hits", 0)
                    / (
                        info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0)
                    )
                    if (
                        info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0)
                    )
                    > 0
                    else 0
                ),
            }
        except Exception as e:
            logger.warning(f"RedisCache.get_stats error: {e}")
            return {"error": str(e)}


class Cache:
    """Singleton cache instance with auto-detection and graceful fallback."""

    _instance: Optional["Cache"] = None
    _backend: Optional[CacheBackend] = None

    def __new__(cls) -> "Cache":
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """Initialize cache backend with fallback logic."""
        import os

        try:
            # Try Redis first
            redis_url = os.getenv("REDIS_URL")
            if redis_url:
                redis_cache = RedisCache(redis_url)
                if redis_cache.is_available():
                    self._backend = redis_cache
                    logger.info("Cache initialized with Redis backend")
                    return
        except Exception as e:
            logger.debug(f"Redis initialization failed: {e}")

        # Fall back to in-memory cache
        max_entries = int(os.getenv("CACHE_MAX_ENTRIES", "10000"))
        self._backend = MemoryCache(max_entries=max_entries)
        logger.info(f"Cache initialized with MemoryCache backend (max {max_entries} entries)")

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            return self._backend.get(key)
        except Exception as e:
            logger.error(f"Cache.get unexpected error for key '{key}': {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache."""
        try:
            return self._backend.set(key, value, ttl)
        except Exception as e:
            logger.error(f"Cache.set unexpected error for key '{key}': {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            return self._backend.delete(key)
        except Exception as e:
            logger.error(f"Cache.delete unexpected error for key '{key}': {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern."""
        try:
            return self._backend.delete_pattern(pattern)
        except Exception as e:
            logger.error(f"Cache.delete_pattern unexpected error for pattern '{pattern}': {e}")
            return 0

    def clear(self) -> bool:
        """Clear entire cache."""
        try:
            return self._backend.clear()
        except Exception as e:
            logger.error(f"Cache.clear unexpected error: {e}")
            return False

    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        try:
            return self._backend.get_stats()
        except Exception as e:
            logger.error(f"Cache.get_stats unexpected error: {e}")
            return {"error": str(e)}


# Predefined cache key namespaces with default TTLs
CACHE_KEYS = {
    "ASSETS_TOP": ("assets:top:", 60),  # Top assets (1 minute)
    "ASSETS_SEARCH": ("assets:search:", 120),  # Search results (2 minutes)
    "ASSETS_DETAIL": ("assets:detail:", 300),  # Asset details (5 minutes)
    "NEWS": ("news:", 180),  # News articles (3 minutes)
    "METRICS": ("metrics:", 60),  # Metrics (1 minute)
    "STRATEGIES": ("strategies:", 600),  # Strategies (10 minutes)
}


def cached(prefix: str = "default", ttl: int = 300):
    """
    Decorator for caching route responses.

    Args:
        prefix: Cache key prefix (e.g., "assets")
        ttl: Time to live in seconds (default 300)

    Usage:
        @app.get("/assets/top")
        @cached(prefix="assets_top", ttl=60)
        async def get_top_assets():
            ...
    """

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key from function name and all arguments
            # Convert args to dict-like structure for consistent JSON serialization
            call_args = {f"arg_{i}": arg for i, arg in enumerate(args)}
            call_args.update(kwargs)
            cache_key = f"{prefix}:{func.__name__}:{json.dumps(call_args, sort_keys=True, default=str)}"

            # Try to get from cache
            cache = Cache()
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_result

            # Cache miss - execute function
            result = await func(*args, **kwargs)

            # Store in cache
            cache.set(cache_key, result, ttl)
            logger.debug(f"Cache miss, stored: {cache_key}")

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key from function name and all arguments
            # Convert args to dict-like structure for consistent JSON serialization
            call_args = {f"arg_{i}": arg for i, arg in enumerate(args)}
            call_args.update(kwargs)
            cache_key = f"{prefix}:{func.__name__}:{json.dumps(call_args, sort_keys=True, default=str)}"

            # Try to get from cache
            cache = Cache()
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_result

            # Cache miss - execute function
            result = func(*args, **kwargs)

            # Store in cache
            cache.set(cache_key, result, ttl)
            logger.debug(f"Cache miss, stored: {cache_key}")

            return result

        # Return async or sync wrapper based on function
        if hasattr(func, "__await__"):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Initialize singleton on module load
_default_cache = Cache()
