"""Scheduled job: memory pruning.

Removes low-value chat_turn entries older than a threshold,
keeping promoted entries and rolling old turns into summaries.
"""

from __future__ import annotations

import logging
from typing import Dict, List

from ..storage.postgres import PostgresStore

logger = logging.getLogger("mcp_memory.jobs.prune")


async def prune_old_chat_turns(
    pg: PostgresStore,
    tenant_id: str,
    older_than_days: int = 30,
) -> Dict[str, int]:
    """Delete non-promoted chat_turn entries older than N days across all scopes.

    Returns dict of {scope_id: deleted_count}.
    """
    results: Dict[str, int] = {}

    # Find all scopes for this tenant
    async with pg._pool.acquire() as conn:
        scope_rows = await conn.fetch(
            "SELECT id FROM scopes WHERE tenant_id = $1",
            tenant_id,
        )

    total_deleted = 0
    for scope_row in scope_rows:
        scope_id = scope_row["id"]
        try:
            count = await pg.delete_old_chat_turns(
                tenant_id, scope_id, older_than_days
            )
            if count > 0:
                results[scope_id] = count
                total_deleted += count
        except Exception:
            logger.exception(
                "Failed to prune chat_turns for scope %s", scope_id
            )

    logger.info(
        "Prune job complete: tenant=%s scopes=%d total_deleted=%d",
        tenant_id,
        len(scope_rows),
        total_deleted,
    )
    return results
