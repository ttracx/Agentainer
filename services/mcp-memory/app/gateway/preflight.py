"""Node preflight: context bootstrap before task execution.

Before executing any task, the node calls this to:
1. Search memory for relevant prior outcomes in the current scope
2. Retrieve the working set from Redis
3. Format results as "Known Context" for injection into the agent prompt
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ..config import Settings
from ..embedding import embed_text
from ..storage.postgres import PostgresStore
from ..storage.redis_cache import RedisCache

logger = logging.getLogger("mcp_memory.gateway.preflight")


class PreflightContext:
    """Assembles prior context for a node before task execution."""

    def __init__(
        self,
        pg: PostgresStore,
        cache: RedisCache,
        settings: Settings,
    ):
        self._pg = pg
        self._cache = cache
        self._settings = settings

    async def get_context(
        self,
        tenant_id: str,
        scope: Dict[str, Optional[str]],
        task_title: str,
        task_description: Optional[str] = None,
        top_k: int = 5,
        include_working_set: bool = True,
    ) -> Dict[str, Any]:
        """Retrieve relevant prior context for a task.

        Returns a dict with:
        - 'memories': list of relevant memory entries (ranked)
        - 'working_set_ids': list of recent memory IDs from Redis
        - 'known_context': formatted string for agent prompt injection
        """
        await self._pg.ensure_tenant(tenant_id)
        scope_id = await self._pg.get_or_create_scope(tenant_id, scope)

        # Build query from task title + description
        query = task_title
        if task_description:
            query = f"{task_title} {task_description}"

        # Search for relevant prior memories
        query_embedding = await embed_text(query, self._settings)

        memories = await self._pg.search_memory(
            tenant_id=tenant_id,
            scope_id=scope_id,
            query_embedding=query_embedding,
            query_text=query,
            top_k=top_k,
            kinds=["task_outcome", "decision", "runbook", "summary"],
        )

        # Get working set
        working_set_ids: List[str] = []
        if include_working_set:
            working_set_ids = await self._cache.get_working_set(
                tenant_id, scope_id
            )

        # Format as "Known Context" for prompt injection
        known_context = self._format_known_context(memories)

        await self._cache.record_search(tenant_id)

        logger.info(
            "preflight: tenant=%s scope=%s task=%r found=%d memories, ws=%d",
            tenant_id,
            scope_id,
            task_title,
            len(memories),
            len(working_set_ids),
        )

        return {
            "memories": memories,
            "working_set_ids": working_set_ids,
            "known_context": known_context,
            "scope_id": scope_id,
        }

    def _format_known_context(self, memories: List[Dict[str, Any]]) -> str:
        """Format retrieved memories as a context block for agent prompts."""
        if not memories:
            return ""

        lines = ["## Known Context (from prior tasks)\n"]
        for i, mem in enumerate(memories, 1):
            kind = mem.get("kind", "unknown")
            title = mem.get("title", "untitled")
            content = mem.get("content", "")
            tags = mem.get("tags", [])
            score = mem.get("score")

            # Truncate content for prompt injection (keep it focused)
            if len(content) > 500:
                content = content[:500] + "..."

            score_str = f" (relevance: {score:.2f})" if score else ""
            tag_str = f" [{', '.join(tags)}]" if tags else ""

            lines.append(
                f"### {i}. [{kind}] {title}{score_str}{tag_str}\n{content}\n"
            )

        return "\n".join(lines)
