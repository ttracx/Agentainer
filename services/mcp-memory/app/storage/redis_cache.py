"""Redis caching layer for MCP Memory Server.

Implements:
- Working-set cache: last N memory IDs per tenant+scope (TTL 6h)
- Search result cache: by query hash + scope (TTL 10-30 min)
- Observability counters
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

import redis.asyncio as aioredis

from ..config import Settings

logger = logging.getLogger("mcp_memory.storage.redis_cache")


class RedisCache:
    """Async Redis cache operations."""

    def __init__(self, client: aioredis.Redis, settings: Settings):
        self._r = client
        self._settings = settings

    @classmethod
    async def create(cls, settings: Settings) -> "RedisCache":
        client = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            retry_on_timeout=True,
        )
        # Verify connection
        await client.ping()
        return cls(client, settings)

    async def close(self) -> None:
        await self._r.close()

    # ── Working Set ──────────────────────────────────────────────────

    def _working_set_key(self, tenant_id: str, scope_id: str) -> str:
        return f"mem:ws:{tenant_id}:{scope_id}"

    async def push_to_working_set(
        self, tenant_id: str, scope_id: str, memory_id: str
    ) -> None:
        """Add a memory ID to the front of the working set for this scope."""
        key = self._working_set_key(tenant_id, scope_id)
        pipe = self._r.pipeline()
        pipe.lrem(key, 0, memory_id)  # Remove duplicates
        pipe.lpush(key, memory_id)
        pipe.ltrim(key, 0, self._settings.working_set_max - 1)
        pipe.expire(key, self._settings.working_set_ttl)
        await pipe.execute()

    async def get_working_set(
        self, tenant_id: str, scope_id: str
    ) -> List[str]:
        """Get the working set memory IDs for this scope."""
        key = self._working_set_key(tenant_id, scope_id)
        return await self._r.lrange(key, 0, -1)

    # ── Search Cache ─────────────────────────────────────────────────

    def _search_cache_key(
        self, tenant_id: str, scope_id: str, query_hash: str
    ) -> str:
        return f"mem:sc:{tenant_id}:{scope_id}:{query_hash}"

    def _hash_query(
        self,
        query: str,
        tags: List[str],
        kinds: List[str],
        top_k: int,
    ) -> str:
        raw = f"{query}|{'|'.join(sorted(tags))}|{'|'.join(sorted(kinds))}|{top_k}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    async def get_cached_search(
        self,
        tenant_id: str,
        scope_id: str,
        query: str,
        tags: List[str],
        kinds: List[str],
        top_k: int,
    ) -> Optional[List[Dict[str, Any]]]:
        """Return cached search results if available."""
        qh = self._hash_query(query, tags, kinds, top_k)
        key = self._search_cache_key(tenant_id, scope_id, qh)
        cached = await self._r.get(key)
        if cached:
            logger.debug("Search cache hit: %s", key)
            await self._increment_counter("mem:stats:search_cache_hits")
            return json.loads(cached)
        await self._increment_counter("mem:stats:search_cache_misses")
        return None

    async def set_cached_search(
        self,
        tenant_id: str,
        scope_id: str,
        query: str,
        tags: List[str],
        kinds: List[str],
        top_k: int,
        results: List[Dict[str, Any]],
    ) -> None:
        """Cache search results."""
        qh = self._hash_query(query, tags, kinds, top_k)
        key = self._search_cache_key(tenant_id, scope_id, qh)
        await self._r.setex(
            key, self._settings.search_cache_ttl, json.dumps(results, default=str)
        )

    async def invalidate_scope_cache(
        self, tenant_id: str, scope_id: str
    ) -> None:
        """Invalidate all search caches for a scope after a write."""
        pattern = f"mem:sc:{tenant_id}:{scope_id}:*"
        cursor = 0
        while True:
            cursor, keys = await self._r.scan(cursor, match=pattern, count=100)
            if keys:
                await self._r.delete(*keys)
            if cursor == 0:
                break

    # ── Observability Counters ───────────────────────────────────────

    async def _increment_counter(self, key: str) -> None:
        pipe = self._r.pipeline()
        pipe.incr(key)
        pipe.expire(key, 86400)  # 24h TTL on counters
        await pipe.execute()

    async def record_write(self, tenant_id: str) -> None:
        await self._increment_counter(f"mem:stats:writes:{tenant_id}")

    async def record_search(self, tenant_id: str) -> None:
        await self._increment_counter(f"mem:stats:searches:{tenant_id}")

    async def record_dedupe_hit(self, tenant_id: str) -> None:
        await self._increment_counter(f"mem:stats:dedupes:{tenant_id}")

    async def get_stats(self, tenant_id: str) -> Dict[str, int]:
        """Retrieve basic stats counters."""
        keys = [
            f"mem:stats:writes:{tenant_id}",
            f"mem:stats:searches:{tenant_id}",
            f"mem:stats:dedupes:{tenant_id}",
            "mem:stats:search_cache_hits",
            "mem:stats:search_cache_misses",
        ]
        values = await self._r.mget(keys)
        return {
            "writes": int(values[0] or 0),
            "searches": int(values[1] or 0),
            "dedupes": int(values[2] or 0),
            "search_cache_hits": int(values[3] or 0),
            "search_cache_misses": int(values[4] or 0),
        }
