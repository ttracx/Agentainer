"""PostgreSQL storage layer for MCP Memory Server.

Handles all durable persistence: memory entries, embeddings, links, attachments, scopes.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import asyncpg

from ..config import Settings

logger = logging.getLogger("mcp_memory.storage.postgres")


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _make_scope_id(tenant_id: str, scope: Dict[str, Optional[str]]) -> str:
    key = f"{tenant_id}|{scope.get('channel_id')}|{scope.get('conversation_id')}|{scope.get('project_id')}|{scope.get('task_id')}"
    return f"sc_{_sha256(key)[:24]}"


def _make_memory_id(content_hash: str) -> str:
    return f"mem_{content_hash[:24]}"


def compute_content_hash(kind: str, title: Optional[str], content: str) -> str:
    normalized = " ".join(content.strip().split())
    return _sha256(f"{kind}|{title or ''}|{normalized}")


class PostgresStore:
    """Async PostgreSQL operations for the memory server."""

    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    @classmethod
    async def create(cls, settings: Settings) -> "PostgresStore":
        pool = await asyncpg.create_pool(
            dsn=settings.pg_dsn,
            min_size=settings.pg_min_pool,
            max_size=settings.pg_max_pool,
        )
        return cls(pool)

    async def close(self) -> None:
        await self._pool.close()

    async def run_migrations(self, migrations_dir: str) -> None:
        """Run SQL migration files in order."""
        import pathlib

        mig_path = pathlib.Path(migrations_dir)
        if not mig_path.exists():
            logger.warning("Migrations directory not found: %s", migrations_dir)
            return

        sql_files = sorted(mig_path.glob("*.sql"))
        async with self._pool.acquire() as conn:
            for f in sql_files:
                logger.info("Running migration: %s", f.name)
                sql = f.read_text()
                await conn.execute(sql)
        logger.info("Migrations complete.")

    # ── Tenant ───────────────────────────────────────────────────────

    async def ensure_tenant(self, tenant_id: str) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO tenants (id, name) VALUES ($1, $2) ON CONFLICT (id) DO NOTHING",
                tenant_id,
                tenant_id,
            )

    # ── Scope ────────────────────────────────────────────────────────

    async def get_or_create_scope(
        self, tenant_id: str, scope: Dict[str, Optional[str]]
    ) -> str:
        scope_id = _make_scope_id(tenant_id, scope)
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO scopes (id, tenant_id, channel_id, conversation_id, project_id, task_id)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (id) DO NOTHING
                """,
                scope_id,
                tenant_id,
                scope.get("channel_id"),
                scope.get("conversation_id"),
                scope.get("project_id"),
                scope.get("task_id"),
            )
        return scope_id

    # ── Memory Write ─────────────────────────────────────────────────

    async def write_memory(
        self,
        tenant_id: str,
        scope_id: str,
        kind: str,
        title: Optional[str],
        content: str,
        tags: List[str],
        source: Optional[str],
        author_agent_id: Optional[str],
        tool_name: Optional[str],
        content_hash: str,
        embedding: List[float],
    ) -> Dict[str, Any]:
        """Upsert a memory entry with its embedding. Returns the row dict."""
        mem_id = _make_memory_id(content_hash)
        normalized_content = " ".join(content.strip().split())

        async with self._pool.acquire() as conn:
            async with conn.transaction():
                # Upsert memory entry
                await conn.execute(
                    """
                    INSERT INTO memory_entries
                        (id, tenant_id, scope_id, kind, title, content, tags,
                         source, author_agent_id, tool_name, content_hash)
                    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
                    ON CONFLICT (tenant_id, scope_id, kind, content_hash)
                    DO UPDATE SET updated_at = now()
                    """,
                    mem_id,
                    tenant_id,
                    scope_id,
                    kind,
                    title,
                    normalized_content,
                    tags,
                    source,
                    author_agent_id,
                    tool_name,
                    content_hash,
                )

                # Upsert embedding
                emb_str = "[" + ",".join(str(v) for v in embedding) + "]"
                await conn.execute(
                    """
                    INSERT INTO memory_embeddings (memory_id, embedding)
                    VALUES ($1, $2::vector)
                    ON CONFLICT (memory_id) DO UPDATE SET embedding = EXCLUDED.embedding
                    """,
                    mem_id,
                    emb_str,
                )

                row = await conn.fetchrow(
                    """
                    SELECT id, kind, title, content, tags, source, author_agent_id,
                           created_at, updated_at
                    FROM memory_entries
                    WHERE id = $1 AND tenant_id = $2
                    """,
                    mem_id,
                    tenant_id,
                )

        return dict(row) if row else {}

    # ── Memory Search (hybrid) ───────────────────────────────────────

    async def search_memory(
        self,
        tenant_id: str,
        scope_id: str,
        query_embedding: List[float],
        query_text: str,
        top_k: int = 10,
        tags: Optional[List[str]] = None,
        kinds: Optional[List[str]] = None,
        time_range_start: Optional[datetime] = None,
        time_range_end: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Hybrid retrieval: vector similarity + keyword (trigram) + metadata filters."""
        emb_str = "[" + ",".join(str(v) for v in query_embedding) + "]"
        kinds_filter = kinds if kinds else None
        tags_filter = tags if tags else None

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                WITH candidates AS (
                    SELECT me.id, me.kind, me.title, me.content, me.tags,
                           me.source, me.author_agent_id,
                           me.created_at, me.updated_at,
                           1 - (mb.embedding <=> $1::vector) AS vec_score
                    FROM memory_entries me
                    JOIN memory_embeddings mb ON mb.memory_id = me.id
                    WHERE me.tenant_id = $2
                      AND me.scope_id = $3
                      AND ($4::text[] IS NULL OR me.kind = ANY($4::text[]))
                      AND ($5::text[] IS NULL OR me.tags && $5::text[])
                      AND ($7::timestamptz IS NULL OR me.created_at >= $7)
                      AND ($8::timestamptz IS NULL OR me.created_at <= $8)
                    ORDER BY mb.embedding <=> $1::vector
                    LIMIT 50
                ),
                keyword AS (
                    SELECT me.id,
                           GREATEST(
                               similarity(me.content, $6),
                               similarity(COALESCE(me.title, ''), $6)
                           ) AS kw_score
                    FROM memory_entries me
                    WHERE me.tenant_id = $2
                      AND me.scope_id = $3
                      AND ($4::text[] IS NULL OR me.kind = ANY($4::text[]))
                      AND ($5::text[] IS NULL OR me.tags && $5::text[])
                      AND ($7::timestamptz IS NULL OR me.created_at >= $7)
                      AND ($8::timestamptz IS NULL OR me.created_at <= $8)
                    ORDER BY kw_score DESC
                    LIMIT 50
                )
                SELECT c.id, c.kind, c.title, c.content, c.tags,
                       c.source, c.author_agent_id,
                       c.created_at, c.updated_at,
                       (c.vec_score * 0.75 + COALESCE(k.kw_score, 0) * 0.25) AS score
                FROM candidates c
                LEFT JOIN keyword k ON k.id = c.id
                ORDER BY score DESC
                LIMIT $9
                """,
                emb_str,
                tenant_id,
                scope_id,
                kinds_filter,
                tags_filter,
                query_text,
                time_range_start,
                time_range_end,
                top_k,
            )

        return [dict(r) for r in rows]

    # ── Memory Get ───────────────────────────────────────────────────

    async def get_memory(
        self, tenant_id: str, memory_id: str
    ) -> Optional[Dict[str, Any]]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, kind, title, content, tags, source, author_agent_id,
                       created_at, updated_at
                FROM memory_entries
                WHERE id = $1 AND tenant_id = $2
                """,
                memory_id,
                tenant_id,
            )
        return dict(row) if row else None

    async def get_attachments(
        self, tenant_id: str, memory_id: str
    ) -> List[Dict[str, Any]]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, memory_id, blob_key, filename, mime_type, bytes, sha256, created_at
                FROM memory_attachments
                WHERE memory_id = $1 AND tenant_id = $2
                """,
                memory_id,
                tenant_id,
            )
        return [dict(r) for r in rows]

    async def get_links_from(
        self, memory_id: str
    ) -> List[Dict[str, Any]]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, from_memory_id, to_memory_id, relation, created_at
                FROM memory_links
                WHERE from_memory_id = $1
                """,
                memory_id,
            )
        return [dict(r) for r in rows]

    async def get_links_to(
        self, memory_id: str
    ) -> List[Dict[str, Any]]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, from_memory_id, to_memory_id, relation, created_at
                FROM memory_links
                WHERE to_memory_id = $1
                """,
                memory_id,
            )
        return [dict(r) for r in rows]

    # ── Memory Link ──────────────────────────────────────────────────

    async def create_link(
        self,
        tenant_id: str,
        from_memory_id: str,
        to_memory_id: str,
        relation: str,
    ) -> Dict[str, Any]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO memory_links (tenant_id, from_memory_id, to_memory_id, relation)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (from_memory_id, to_memory_id, relation) DO NOTHING
                RETURNING id, from_memory_id, to_memory_id, relation, created_at
                """,
                tenant_id,
                from_memory_id,
                to_memory_id,
                relation,
            )
            if row is None:
                # Link already existed, fetch it
                row = await conn.fetchrow(
                    """
                    SELECT id, from_memory_id, to_memory_id, relation, created_at
                    FROM memory_links
                    WHERE from_memory_id = $1 AND to_memory_id = $2 AND relation = $3
                    """,
                    from_memory_id,
                    to_memory_id,
                    relation,
                )
        return dict(row) if row else {}

    # ── Attachments ──────────────────────────────────────────────────

    async def write_attachment(
        self,
        attachment_id: str,
        tenant_id: str,
        memory_id: str,
        blob_key: str,
        filename: str,
        mime_type: str,
        byte_count: int,
        sha256_hash: str,
    ) -> Dict[str, Any]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO memory_attachments
                    (id, tenant_id, memory_id, blob_key, filename, mime_type, bytes, sha256)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (id) DO NOTHING
                RETURNING id, memory_id, blob_key, filename, mime_type, bytes, sha256, created_at
                """,
                attachment_id,
                tenant_id,
                memory_id,
                blob_key,
                filename,
                mime_type,
                byte_count,
                sha256_hash,
            )
            if row is None:
                row = await conn.fetchrow(
                    "SELECT * FROM memory_attachments WHERE id = $1",
                    attachment_id,
                )
        return dict(row) if row else {}

    async def get_attachment(
        self, tenant_id: str, attachment_id: str
    ) -> Optional[Dict[str, Any]]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, memory_id, blob_key, filename, mime_type, bytes, sha256, created_at
                FROM memory_attachments
                WHERE id = $1 AND tenant_id = $2
                """,
                attachment_id,
                tenant_id,
            )
        return dict(row) if row else None

    # ── Scope Entries (for summarization) ────────────────────────────

    async def get_scope_entries(
        self,
        tenant_id: str,
        scope_id: str,
        max_entries: int = 50,
        exclude_kinds: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        exclude = exclude_kinds or []
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, kind, title, content, tags, created_at
                FROM memory_entries
                WHERE tenant_id = $1 AND scope_id = $2
                  AND ($3::text[] = '{}' OR kind != ALL($3::text[]))
                ORDER BY created_at DESC
                LIMIT $4
                """,
                tenant_id,
                scope_id,
                exclude,
                max_entries,
            )
        return [dict(r) for r in rows]

    # ── Bulk queries for jobs ────────────────────────────────────────

    async def get_promoted_candidates(
        self, tenant_id: str, min_references: int = 3, days: int = 30
    ) -> List[Dict[str, Any]]:
        """Find task_outcome entries referenced more than min_references times."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT me.id, me.kind, me.title, me.tags, me.created_at,
                       COUNT(ml.id) AS ref_count
                FROM memory_entries me
                JOIN memory_links ml ON ml.to_memory_id = me.id
                WHERE me.tenant_id = $1
                  AND me.kind = 'task_outcome'
                  AND me.created_at >= now() - ($3 || ' days')::interval
                  AND NOT ('promoted' = ANY(me.tags))
                GROUP BY me.id
                HAVING COUNT(ml.id) >= $2
                """,
                tenant_id,
                min_references,
                str(days),
            )
        return [dict(r) for r in rows]

    async def add_tag(self, memory_id: str, tag: str) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE memory_entries
                SET tags = array_append(tags, $2), updated_at = now()
                WHERE id = $1 AND NOT ($2 = ANY(tags))
                """,
                memory_id,
                tag,
            )

    async def delete_old_chat_turns(
        self, tenant_id: str, scope_id: str, older_than_days: int = 30
    ) -> int:
        """Delete low-value chat_turn entries older than N days."""
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                DELETE FROM memory_entries
                WHERE tenant_id = $1
                  AND scope_id = $2
                  AND kind = 'chat_turn'
                  AND created_at < now() - ($3 || ' days')::interval
                  AND NOT ('promoted' = ANY(tags))
                """,
                tenant_id,
                scope_id,
                str(older_than_days),
            )
            # result is like "DELETE 5"
            count = int(result.split()[-1]) if result else 0
        return count
