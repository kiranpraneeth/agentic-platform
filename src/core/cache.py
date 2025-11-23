"""Redis caching layer for performance optimization."""

import json
from typing import Any, Optional

import redis.asyncio as redis
from redis.asyncio import Redis

from src.core.config import settings
from src.core.logging import get_logger
from src.core.metrics import cache_hits_total, cache_misses_total

logger = get_logger(__name__)

# Redis client instance
_redis_client: Optional[Redis] = None


async def get_redis() -> Redis:
    """Get Redis client instance.

    Returns:
        Redis client
    """
    global _redis_client

    if _redis_client is None:
        _redis_client = redis.from_url(
            str(settings.REDIS_URL),
            encoding="utf-8",
            decode_responses=True,
            max_connections=settings.REDIS_POOL_SIZE,
        )

    return _redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis_client

    if _redis_client:
        await _redis_client.close()
        _redis_client = None


class CacheService:
    """Redis cache service for application data."""

    def __init__(self, redis_client: Optional[Redis] = None):
        """Initialize cache service.

        Args:
            redis_client: Optional Redis client (for testing)
        """
        self._redis = redis_client
        self._enabled = True

    async def _get_redis(self) -> Redis:
        """Get Redis client."""
        if self._redis:
            return self._redis
        return await get_redis()

    async def get(
        self,
        key: str,
        cache_type: str = "general",
    ) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key
            cache_type: Type of cache for metrics

        Returns:
            Cached value or None if not found
        """
        if not self._enabled:
            return None

        try:
            redis_client = await self._get_redis()
            value = await redis_client.get(key)

            if value is not None:
                cache_hits_total.labels(cache_type=cache_type).inc()
                logger.debug("cache_hit", key=key, cache_type=cache_type)
                return json.loads(value)
            else:
                cache_misses_total.labels(cache_type=cache_type).inc()
                logger.debug("cache_miss", key=key, cache_type=cache_type)
                return None

        except Exception as e:
            logger.error("cache_get_error", error=str(e), key=key)
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        cache_type: str = "general",
    ) -> bool:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None = no expiration)
            cache_type: Type of cache for metrics

        Returns:
            True if successful
        """
        if not self._enabled:
            return False

        try:
            redis_client = await self._get_redis()
            serialized = json.dumps(value)

            if ttl:
                await redis_client.setex(key, ttl, serialized)
            else:
                await redis_client.set(key, serialized)

            logger.debug("cache_set", key=key, ttl=ttl, cache_type=cache_type)
            return True

        except Exception as e:
            logger.error("cache_set_error", error=str(e), key=key)
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if successful
        """
        if not self._enabled:
            return False

        try:
            redis_client = await self._get_redis()
            await redis_client.delete(key)
            logger.debug("cache_delete", key=key)
            return True

        except Exception as e:
            logger.error("cache_delete_error", error=str(e), key=key)
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern.

        Args:
            pattern: Key pattern (e.g., "agent:*")

        Returns:
            Number of keys deleted
        """
        if not self._enabled:
            return 0

        try:
            redis_client = await self._get_redis()
            keys = []
            async for key in redis_client.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                deleted = await redis_client.delete(*keys)
                logger.info("cache_delete_pattern", pattern=pattern, count=deleted)
                return deleted

            return 0

        except Exception as e:
            logger.error("cache_delete_pattern_error", error=str(e), pattern=pattern)
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        if not self._enabled:
            return False

        try:
            redis_client = await self._get_redis()
            return await redis_client.exists(key) > 0

        except Exception as e:
            logger.error("cache_exists_error", error=str(e), key=key)
            return False

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a counter.

        Args:
            key: Cache key
            amount: Amount to increment by

        Returns:
            New value or None on error
        """
        if not self._enabled:
            return None

        try:
            redis_client = await self._get_redis()
            return await redis_client.incrby(key, amount)

        except Exception as e:
            logger.error("cache_increment_error", error=str(e), key=key)
            return None

    async def set_with_lock(
        self,
        key: str,
        value: Any,
        lock_timeout: int = 10,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set value with distributed lock.

        Args:
            key: Cache key
            value: Value to cache
            lock_timeout: Lock timeout in seconds
            ttl: Value TTL in seconds

        Returns:
            True if successful
        """
        if not self._enabled:
            return False

        lock_key = f"lock:{key}"

        try:
            redis_client = await self._get_redis()

            # Try to acquire lock
            lock_acquired = await redis_client.set(
                lock_key, "1", nx=True, ex=lock_timeout
            )

            if not lock_acquired:
                logger.warning("cache_lock_failed", key=key)
                return False

            try:
                # Set the value
                await self.set(key, value, ttl)
                return True

            finally:
                # Release lock
                await redis_client.delete(lock_key)

        except Exception as e:
            logger.error("cache_set_with_lock_error", error=str(e), key=key)
            return False


# Cache key generators
def agent_cache_key(tenant_id: str, agent_id: str) -> str:
    """Generate cache key for agent.

    Args:
        tenant_id: Tenant ID
        agent_id: Agent ID

    Returns:
        Cache key
    """
    return f"agent:{tenant_id}:{agent_id}"


def workflow_cache_key(tenant_id: str, workflow_id: str) -> str:
    """Generate cache key for workflow.

    Args:
        tenant_id: Tenant ID
        workflow_id: Workflow ID

    Returns:
        Cache key
    """
    return f"workflow:{tenant_id}:{workflow_id}"


def mcp_server_cache_key(tenant_id: str, server_id: str) -> str:
    """Generate cache key for MCP server.

    Args:
        tenant_id: Tenant ID
        server_id: Server ID

    Returns:
        Cache key
    """
    return f"mcp_server:{tenant_id}:{server_id}"


def embedding_cache_key(text: str, model: str) -> str:
    """Generate cache key for embeddings.

    Args:
        text: Text to embed
        model: Model name

    Returns:
        Cache key
    """
    import hashlib

    text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
    return f"embedding:{model}:{text_hash}"


def rag_search_cache_key(
    collection_id: str, query: str, top_k: int
) -> str:
    """Generate cache key for RAG search results.

    Args:
        collection_id: Collection ID
        query: Search query
        top_k: Number of results

    Returns:
        Cache key
    """
    import hashlib

    query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
    return f"rag_search:{collection_id}:{query_hash}:{top_k}"


# Global cache instance
cache = CacheService()
