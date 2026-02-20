"""Scheduled job: scope summarization.

Creates durable summary entries for active scopes, linking to source entries.
Run daily or weekly depending on activity.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from ..config import Settings
from ..embedding import embed_text
from ..storage.postgres import PostgresStore, compute_content_hash
from ..storage.redis_cache import RedisCache

logger = logging.getLogger("mcp_memory.jobs.summarize")


async def summarize_active_scopes(
    pg: PostgresStore,
    cache: RedisCache,
    settings: Settings,
    tenant_id: str,
    max_entries_per_scope: int = 50,
    mode: str = "brief",
) -> List[str]:
    """Summarize all active scopes for a tenant.

    Returns list of created summary memory IDs.
    """
    created_ids: List[str] = []

    # Find scopes with recent activity
    async with pg._pool.acquire() as conn:
        scope_rows = await conn.fetch(
            """
            SELECT DISTINCT s.id AS scope_id
            FROM scopes s
            JOIN memory_entries me ON me.scope_id = s.id
            WHERE s.tenant_id = $1
              AND me.created_at >= now() - interval '7 days'
              AND me.kind != 'summary'
            """,
            tenant_id,
        )

    for scope_row in scope_rows:
        scope_id = scope_row["scope_id"]
        try:
            summary_id = await _summarize_scope(
                pg, cache, settings, tenant_id, scope_id,
                max_entries_per_scope, mode,
            )
            if summary_id:
                created_ids.append(summary_id)
        except Exception:
            logger.exception(
                "Failed to summarize scope %s for tenant %s",
                scope_id,
                tenant_id,
            )

    logger.info(
        "Summarization job complete: tenant=%s scopes=%d summaries=%d",
        tenant_id,
        len(scope_rows),
        len(created_ids),
    )
    return created_ids


async def _summarize_scope(
    pg: PostgresStore,
    cache: RedisCache,
    settings: Settings,
    tenant_id: str,
    scope_id: str,
    max_entries: int,
    mode: str,
) -> Optional[str]:
    """Create a summary for a single scope."""
    entries = await pg.get_scope_entries(
        tenant_id, scope_id,
        max_entries=max_entries,
        exclude_kinds=["summary"],
    )

    if not entries:
        return None

    # Build summary text
    if mode == "brief":
        lines = []
        for e in entries[:20]:
            title_part = f" {e['title']}" if e.get("title") else ""
            content_preview = e["content"][:200]
            lines.append(f"[{e['kind']}]{title_part}: {content_preview}")
        summary_content = (
            f"Weekly summary ({len(entries)} entries):\n" + "\n".join(lines)
        )
    else:
        lines = []
        for e in entries:
            title_part = f" {e['title']}" if e.get("title") else ""
            lines.append(f"[{e['kind']}]{title_part}: {e['content']}")
        summary_content = (
            f"Full summary ({len(entries)} entries):\n" + "\n---\n".join(lines)
        )

    content_hash = compute_content_hash("summary", "weekly_summary", summary_content)
    embedding = await embed_text(summary_content, settings)

    row = await pg.write_memory(
        tenant_id=tenant_id,
        scope_id=scope_id,
        kind="summary",
        title="weekly_summary",
        content=summary_content,
        tags=["auto_summary", "scheduled", mode],
        source="system",
        author_agent_id=None,
        tool_name=None,
        content_hash=content_hash,
        embedding=embedding,
    )

    if not row:
        return None

    # Link summary to source entries
    for e in entries:
        try:
            await pg.create_link(
                tenant_id=tenant_id,
                from_memory_id=row["id"],
                to_memory_id=e["id"],
                relation="derived_from",
            )
        except Exception:
            pass

    await cache.invalidate_scope_cache(tenant_id, scope_id)
    logger.info("Created summary %s for scope %s", row["id"], scope_id)
    return row["id"]
