"""Scheduled job: memory promotion.

Promotes frequently referenced task_outcome entries to long-term memory
by adding the 'promoted' tag. This ensures high-value knowledge is
prioritized in retrieval.
"""

from __future__ import annotations

import logging
from typing import List

from ..storage.postgres import PostgresStore

logger = logging.getLogger("mcp_memory.jobs.promote")


async def promote_high_value_memories(
    pg: PostgresStore,
    tenant_id: str,
    min_references: int = 3,
    lookback_days: int = 30,
) -> List[str]:
    """Find and promote task_outcome entries referenced >= min_references times.

    Returns list of promoted memory IDs.
    """
    candidates = await pg.get_promoted_candidates(
        tenant_id, min_references, lookback_days
    )

    promoted_ids: List[str] = []
    for c in candidates:
        try:
            await pg.add_tag(c["id"], "promoted")
            promoted_ids.append(c["id"])
            logger.info(
                "Promoted memory %s (ref_count=%d)", c["id"], c["ref_count"]
            )
        except Exception:
            logger.exception("Failed to promote memory %s", c["id"])

    logger.info(
        "Promotion job complete: tenant=%s candidates=%d promoted=%d",
        tenant_id,
        len(candidates),
        len(promoted_ids),
    )
    return promoted_ids
