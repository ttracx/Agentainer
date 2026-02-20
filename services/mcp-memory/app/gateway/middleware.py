"""Gateway middleware hooks for automatic memory writes.

Two hooks that integrate with the OpenClaw Gateway:

Hook A: on_message_received
  - Write user messages as kind='chat_turn' (optional)
  - Update Redis working set

Hook B: on_task_completed / on_tool_completed
  - Write kind='task_outcome' with final result, key steps, tool used, tags, artifact links
  - Always fires on task/tool completion for durable knowledge capture

These hooks are designed to be called by the Gateway's event pipeline.
They are NOT FastAPI middleware (despite the filename); they are
async functions the Gateway invokes at the appropriate lifecycle points.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ..config import Settings
from ..embedding import embed_text
from ..storage.postgres import PostgresStore, compute_content_hash
from ..storage.redis_cache import RedisCache

logger = logging.getLogger("mcp_memory.gateway.middleware")


class GatewayMemoryHooks:
    """Hooks the Gateway calls to automatically persist memory."""

    def __init__(
        self,
        pg: PostgresStore,
        cache: RedisCache,
        settings: Settings,
    ):
        self._pg = pg
        self._cache = cache
        self._settings = settings

    async def on_message_received(
        self,
        tenant_id: str,
        scope: Dict[str, Optional[str]],
        content: str,
        author_agent_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Hook A: Write a chat_turn memory entry on incoming message.

        Returns the memory_id if written, or None if skipped/deduped.
        """
        if not content or not content.strip():
            return None

        try:
            await self._pg.ensure_tenant(tenant_id)
            scope_id = await self._pg.get_or_create_scope(tenant_id, scope)

            content_hash = compute_content_hash("chat_turn", None, content)
            embedding = await embed_text(content, self._settings)

            row = await self._pg.write_memory(
                tenant_id=tenant_id,
                scope_id=scope_id,
                kind="chat_turn",
                title=None,
                content=content,
                tags=tags or [],
                source="gateway",
                author_agent_id=author_agent_id,
                tool_name=None,
                content_hash=content_hash,
                embedding=embedding,
            )

            if row:
                mem_id = row["id"]
                await self._cache.push_to_working_set(tenant_id, scope_id, mem_id)
                await self._cache.record_write(tenant_id)
                logger.info(
                    "on_message_received: wrote chat_turn %s scope=%s",
                    mem_id,
                    scope_id,
                )
                return mem_id

        except Exception:
            # Graceful degradation: log error, don't block the message pipeline
            logger.exception("on_message_received failed (non-blocking)")

        return None

    async def on_task_completed(
        self,
        tenant_id: str,
        scope: Dict[str, Optional[str]],
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
        author_agent_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        artifact_memory_ids: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Hook B: Write a task_outcome memory entry on task/tool completion.

        Args:
            title: Short description of what was accomplished.
            content: Full result including key steps, findings, outputs.
            tags: Classification tags (e.g., ['docker', 'infra', 'bugfix']).
            tool_name: Tool used (e.g., 'browser_use', 'computer_use').
            artifact_memory_ids: IDs of related memory entries to link.

        Returns the memory_id if written, or None on failure.
        """
        if not content or not content.strip():
            return None

        try:
            await self._pg.ensure_tenant(tenant_id)
            scope_id = await self._pg.get_or_create_scope(tenant_id, scope)

            all_tags = list(tags or [])
            if tool_name and tool_name not in all_tags:
                all_tags.append(tool_name)

            content_hash = compute_content_hash("task_outcome", title, content)
            embed_input = f"{title} {content}"
            embedding = await embed_text(embed_input, self._settings)

            row = await self._pg.write_memory(
                tenant_id=tenant_id,
                scope_id=scope_id,
                kind="task_outcome",
                title=title,
                content=content,
                tags=all_tags,
                source="gateway",
                author_agent_id=author_agent_id,
                tool_name=tool_name,
                content_hash=content_hash,
                embedding=embedding,
            )

            if row:
                mem_id = row["id"]
                await self._cache.push_to_working_set(tenant_id, scope_id, mem_id)
                await self._cache.invalidate_scope_cache(tenant_id, scope_id)
                await self._cache.record_write(tenant_id)

                # Link to artifact memory entries if provided
                if artifact_memory_ids:
                    for artifact_id in artifact_memory_ids:
                        try:
                            await self._pg.create_link(
                                tenant_id=tenant_id,
                                from_memory_id=mem_id,
                                to_memory_id=artifact_id,
                                relation="related",
                            )
                        except Exception:
                            logger.warning(
                                "Failed to link task_outcome %s to artifact %s",
                                mem_id,
                                artifact_id,
                            )

                logger.info(
                    "on_task_completed: wrote task_outcome %s title=%r scope=%s",
                    mem_id,
                    title,
                    scope_id,
                )
                return mem_id

        except Exception:
            logger.exception("on_task_completed failed (non-blocking)")

        return None

    async def on_tool_completed(
        self,
        tenant_id: str,
        scope: Dict[str, Optional[str]],
        tool_name: str,
        result_summary: str,
        author_agent_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Convenience wrapper: write tool completion as a task_outcome."""
        return await self.on_task_completed(
            tenant_id=tenant_id,
            scope=scope,
            title=f"Tool result: {tool_name}",
            content=result_summary,
            tags=tags,
            author_agent_id=author_agent_id,
            tool_name=tool_name,
        )
