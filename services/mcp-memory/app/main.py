"""MCP Memory Server — FastAPI application entry point.

Exposes MCP tools as HTTP endpoints for Gateway and Node consumption:
- /tools/memory.write
- /tools/memory.search
- /tools/memory.get
- /tools/memory.link
- /tools/memory.summarize_scope
- /tools/memory.attach_blob
- /tools/memory.fetch_blob
- /health
- /stats
"""

from __future__ import annotations

import base64
import hashlib
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from .config import Settings, get_settings
from .embedding import embed_text
from .models import (
    AttachBlobIn,
    AttachmentOut,
    FetchBlobIn,
    LinkOut,
    MemoryGetIn,
    MemoryGetOut,
    MemoryLinkIn,
    MemoryOut,
    MemorySearchIn,
    MemoryWriteIn,
    SummarizeScopeIn,
)
from .storage.blob import BlobStore
from .storage.postgres import PostgresStore, compute_content_hash
from .storage.redis_cache import RedisCache

logger = logging.getLogger("mcp_memory")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and teardown storage backends."""
    settings = get_settings()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    logger.info("Starting MCP Memory Server...")

    # Initialize storage
    pg = await PostgresStore.create(settings)
    await pg.run_migrations(settings.migrations_dir)

    cache = await RedisCache.create(settings)
    blob = BlobStore(settings)
    await blob.initialize()

    # Store on app state
    app.state.pg = pg
    app.state.cache = cache
    app.state.blob = blob
    app.state.settings = settings

    logger.info("MCP Memory Server ready.")
    yield

    # Cleanup
    await pg.close()
    await cache.close()
    logger.info("MCP Memory Server shut down.")


app = FastAPI(title="mcp-memory", version="1.0.0", lifespan=lifespan)


# ── Audit logging middleware ─────────────────────────────────────────


@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    """Log every tool call with actor, latency, and path."""
    start = time.monotonic()
    response = await call_next(request)
    elapsed_ms = (time.monotonic() - start) * 1000

    if request.url.path.startswith("/tools/"):
        logger.info(
            "AUDIT path=%s method=%s status=%d latency_ms=%.1f",
            request.url.path,
            request.method,
            response.status_code,
            elapsed_ms,
        )
    return response


# ── Health ───────────────────────────────────────────────────────────


@app.get("/health")
async def health():
    """Health check endpoint."""
    try:
        pg: PostgresStore = app.state.pg
        cache: RedisCache = app.state.cache
        # Quick connectivity checks
        async with pg._pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        await cache._r.ping()
        return {"status": "ok", "postgres": "ok", "redis": "ok"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "error": str(e)},
        )


@app.get("/stats/{tenant_id}")
async def stats(tenant_id: str):
    """Return observability stats for a tenant."""
    cache: RedisCache = app.state.cache
    return await cache.get_stats(tenant_id)


# ── memory.write ─────────────────────────────────────────────────────


@app.post("/tools/memory.write", response_model=MemoryOut)
async def memory_write(payload: MemoryWriteIn):
    """Persist a memory entry with embedding. Idempotent via content_hash dedupe."""
    pg: PostgresStore = app.state.pg
    cache: RedisCache = app.state.cache
    settings: Settings = app.state.settings

    # Ensure tenant
    await pg.ensure_tenant(payload.tenant_id)

    # Resolve scope
    scope_dict = payload.scope.model_dump()
    scope_id = await pg.get_or_create_scope(payload.tenant_id, scope_dict)

    # Compute content hash for dedupe
    content_hash = compute_content_hash(
        payload.kind, payload.title, payload.content
    )

    # Generate embedding
    embed_input = f"{payload.title or ''} {payload.content}"
    embedding = await embed_text(embed_input, settings)

    # Write to Postgres
    row = await pg.write_memory(
        tenant_id=payload.tenant_id,
        scope_id=scope_id,
        kind=payload.kind,
        title=payload.title,
        content=payload.content,
        tags=payload.tags,
        source=payload.source,
        author_agent_id=payload.author_agent_id,
        tool_name=payload.tool_name,
        content_hash=content_hash,
        embedding=embedding,
    )

    if not row:
        raise HTTPException(status_code=500, detail="Memory write failed")

    # Update Redis working set + invalidate search cache
    await cache.push_to_working_set(payload.tenant_id, scope_id, row["id"])
    await cache.invalidate_scope_cache(payload.tenant_id, scope_id)
    await cache.record_write(payload.tenant_id)

    return MemoryOut(
        id=row["id"],
        kind=row["kind"],
        title=row["title"],
        content=row["content"],
        tags=row["tags"] or [],
        source=row.get("source"),
        author_agent_id=row.get("author_agent_id"),
        created_at=row["created_at"],
        updated_at=row.get("updated_at"),
    )


# ── memory.search ────────────────────────────────────────────────────


@app.post("/tools/memory.search", response_model=List[MemoryOut])
async def memory_search(payload: MemorySearchIn):
    """Hybrid retrieval: vector similarity + keyword (trigram) + metadata filters."""
    pg: PostgresStore = app.state.pg
    cache: RedisCache = app.state.cache
    settings: Settings = app.state.settings

    # Ensure tenant + scope
    await pg.ensure_tenant(payload.tenant_id)
    scope_dict = payload.scope_filter.model_dump()
    scope_id = await pg.get_or_create_scope(payload.tenant_id, scope_dict)

    # Check search cache first
    cached = await cache.get_cached_search(
        payload.tenant_id,
        scope_id,
        payload.query,
        payload.tags,
        payload.kinds,
        payload.top_k,
    )
    if cached is not None:
        return [
            MemoryOut(
                id=r["id"],
                kind=r["kind"],
                title=r.get("title"),
                content=r["content"],
                tags=r.get("tags", []),
                source=r.get("source"),
                author_agent_id=r.get("author_agent_id"),
                created_at=r["created_at"],
                score=r.get("score"),
            )
            for r in cached
        ]

    # Generate query embedding
    query_embedding = await embed_text(payload.query, settings)

    # Hybrid search
    rows = await pg.search_memory(
        tenant_id=payload.tenant_id,
        scope_id=scope_id,
        query_embedding=query_embedding,
        query_text=payload.query,
        top_k=payload.top_k,
        tags=payload.tags or None,
        kinds=payload.kinds or None,
        time_range_start=payload.time_range_start,
        time_range_end=payload.time_range_end,
    )

    # Cache results
    await cache.set_cached_search(
        payload.tenant_id,
        scope_id,
        payload.query,
        payload.tags,
        payload.kinds,
        payload.top_k,
        rows,
    )
    await cache.record_search(payload.tenant_id)

    return [
        MemoryOut(
            id=r["id"],
            kind=r["kind"],
            title=r.get("title"),
            content=r["content"],
            tags=r.get("tags", []),
            source=r.get("source"),
            author_agent_id=r.get("author_agent_id"),
            created_at=r["created_at"],
            updated_at=r.get("updated_at"),
            score=r.get("score"),
        )
        for r in rows
    ]


# ── memory.get ───────────────────────────────────────────────────────


@app.post("/tools/memory.get", response_model=MemoryGetOut)
async def memory_get(payload: MemoryGetIn):
    """Fetch full memory entry with attachments and links."""
    pg: PostgresStore = app.state.pg

    row = await pg.get_memory(payload.tenant_id, payload.memory_id)
    if not row:
        raise HTTPException(status_code=404, detail="Memory entry not found")

    attachments = await pg.get_attachments(payload.tenant_id, payload.memory_id)
    links_from = await pg.get_links_from(payload.memory_id)
    links_to = await pg.get_links_to(payload.memory_id)

    entry = MemoryOut(
        id=row["id"],
        kind=row["kind"],
        title=row.get("title"),
        content=row["content"],
        tags=row.get("tags", []),
        source=row.get("source"),
        author_agent_id=row.get("author_agent_id"),
        created_at=row["created_at"],
        updated_at=row.get("updated_at"),
    )

    return MemoryGetOut(
        entry=entry,
        attachments=[
            AttachmentOut(
                id=a["id"],
                memory_id=a["memory_id"],
                blob_key=a["blob_key"],
                filename=a["filename"],
                mime_type=a["mime_type"],
                bytes=a["bytes"],
                sha256=a["sha256"],
                created_at=a["created_at"],
            )
            for a in attachments
        ],
        linked_from=[
            LinkOut(
                id=l["id"],
                from_memory_id=l["from_memory_id"],
                to_memory_id=l["to_memory_id"],
                relation=l["relation"],
                created_at=l["created_at"],
            )
            for l in links_from
        ],
        linked_to=[
            LinkOut(
                id=l["id"],
                from_memory_id=l["from_memory_id"],
                to_memory_id=l["to_memory_id"],
                relation=l["relation"],
                created_at=l["created_at"],
            )
            for l in links_to
        ],
    )


# ── memory.link ──────────────────────────────────────────────────────


@app.post("/tools/memory.link", response_model=LinkOut)
async def memory_link(payload: MemoryLinkIn):
    """Create a relationship between two memory entries."""
    pg: PostgresStore = app.state.pg

    # Validate both entries exist and belong to tenant
    from_entry = await pg.get_memory(payload.tenant_id, payload.from_memory_id)
    to_entry = await pg.get_memory(payload.tenant_id, payload.to_memory_id)

    if not from_entry:
        raise HTTPException(
            status_code=404,
            detail=f"Source memory entry not found: {payload.from_memory_id}",
        )
    if not to_entry:
        raise HTTPException(
            status_code=404,
            detail=f"Target memory entry not found: {payload.to_memory_id}",
        )

    row = await pg.create_link(
        tenant_id=payload.tenant_id,
        from_memory_id=payload.from_memory_id,
        to_memory_id=payload.to_memory_id,
        relation=payload.relation,
    )

    return LinkOut(
        id=row["id"],
        from_memory_id=row["from_memory_id"],
        to_memory_id=row["to_memory_id"],
        relation=row["relation"],
        created_at=row["created_at"],
    )


# ── memory.summarize_scope ───────────────────────────────────────────


@app.post("/tools/memory.summarize_scope", response_model=MemoryOut)
async def memory_summarize_scope(payload: SummarizeScopeIn):
    """Create a summary of recent memory entries in the given scope.

    The summary is stored as a new memory entry (kind='summary') and linked
    to each source entry with relation='derived_from'.
    """
    pg: PostgresStore = app.state.pg
    cache: RedisCache = app.state.cache
    settings: Settings = app.state.settings

    await pg.ensure_tenant(payload.tenant_id)
    scope_dict = payload.scope.model_dump()
    scope_id = await pg.get_or_create_scope(payload.tenant_id, scope_dict)

    # Fetch recent entries (exclude existing summaries to avoid recursion)
    entries = await pg.get_scope_entries(
        payload.tenant_id,
        scope_id,
        max_entries=payload.max_entries,
        exclude_kinds=["summary"],
    )

    if not entries:
        raise HTTPException(status_code=404, detail="No entries to summarize")

    # Build summary content from entries
    if payload.mode == "brief":
        lines = []
        for e in entries[:20]:
            prefix = f"[{e['kind']}]"
            title_part = f" {e['title']}" if e.get("title") else ""
            content_preview = e["content"][:200]
            lines.append(f"{prefix}{title_part}: {content_preview}")
        summary_content = (
            f"Scope summary ({len(entries)} entries, showing top {min(len(entries), 20)}):\n"
            + "\n".join(lines)
        )
    else:
        lines = []
        for e in entries:
            prefix = f"[{e['kind']}]"
            title_part = f" {e['title']}" if e.get("title") else ""
            lines.append(f"{prefix}{title_part}: {e['content']}")
        summary_content = (
            f"Full scope summary ({len(entries)} entries):\n"
            + "\n---\n".join(lines)
        )

    # Write summary as a new memory entry
    content_hash = compute_content_hash("summary", "scope_summary", summary_content)
    embedding = await embed_text(summary_content, settings)

    row = await pg.write_memory(
        tenant_id=payload.tenant_id,
        scope_id=scope_id,
        kind="summary",
        title="scope_summary",
        content=summary_content,
        tags=["auto_summary", payload.mode],
        source="system",
        author_agent_id=None,
        tool_name=None,
        content_hash=content_hash,
        embedding=embedding,
    )

    if not row:
        raise HTTPException(status_code=500, detail="Failed to write summary")

    # Link summary to source entries
    for e in entries:
        try:
            await pg.create_link(
                tenant_id=payload.tenant_id,
                from_memory_id=row["id"],
                to_memory_id=e["id"],
                relation="derived_from",
            )
        except Exception:
            # Non-critical: log and continue
            logger.warning(
                "Failed to link summary %s to entry %s", row["id"], e["id"]
            )

    await cache.invalidate_scope_cache(payload.tenant_id, scope_id)

    return MemoryOut(
        id=row["id"],
        kind=row["kind"],
        title=row["title"],
        content=row["content"],
        tags=row["tags"] or [],
        source=row.get("source"),
        created_at=row["created_at"],
        updated_at=row.get("updated_at"),
    )


# ── memory.attach_blob ──────────────────────────────────────────────


@app.post("/tools/memory.attach_blob", response_model=AttachmentOut)
async def memory_attach_blob(payload: AttachBlobIn):
    """Upload an attachment to blob store and link to a memory entry."""
    pg: PostgresStore = app.state.pg
    blob: BlobStore = app.state.blob

    # Verify memory entry exists
    entry = await pg.get_memory(payload.tenant_id, payload.memory_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Memory entry not found")

    # Decode base64 data
    try:
        data = base64.b64decode(payload.data_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 data")

    # Upload to blob store
    blob_key = BlobStore.make_blob_key(
        payload.tenant_id, payload.memory_id, payload.filename
    )
    await blob.upload(blob_key, data, payload.mime_type)

    # Compute attachment metadata
    sha256_hash = BlobStore.compute_sha256(data)
    attachment_id = f"att_{sha256_hash[:24]}"

    # Write attachment record
    row = await pg.write_attachment(
        attachment_id=attachment_id,
        tenant_id=payload.tenant_id,
        memory_id=payload.memory_id,
        blob_key=blob_key,
        filename=payload.filename,
        mime_type=payload.mime_type,
        byte_count=len(data),
        sha256_hash=sha256_hash,
    )

    return AttachmentOut(
        id=row["id"],
        memory_id=row["memory_id"],
        blob_key=row["blob_key"],
        filename=row["filename"],
        mime_type=row["mime_type"],
        bytes=row["bytes"],
        sha256=row["sha256"],
        created_at=row["created_at"],
    )


# ── memory.fetch_blob ───────────────────────────────────────────────


@app.post("/tools/memory.fetch_blob")
async def memory_fetch_blob(payload: FetchBlobIn):
    """Retrieve an attachment by ID. Returns metadata + download URL or base64 data."""
    pg: PostgresStore = app.state.pg
    blob_store: BlobStore = app.state.blob

    attachment = await pg.get_attachment(payload.tenant_id, payload.attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    # Try presigned URL first (S3)
    url = await blob_store.generate_presigned_url(attachment["blob_key"])
    if url:
        return {
            "attachment": AttachmentOut(
                id=attachment["id"],
                memory_id=attachment["memory_id"],
                blob_key=attachment["blob_key"],
                filename=attachment["filename"],
                mime_type=attachment["mime_type"],
                bytes=attachment["bytes"],
                sha256=attachment["sha256"],
                created_at=attachment["created_at"],
                download_url=url,
            ),
            "data_base64": None,
        }

    # Fallback: return base64 data (local/dev mode)
    data = await blob_store.download(attachment["blob_key"])
    data_b64 = base64.b64encode(data).decode() if data else None

    return {
        "attachment": AttachmentOut(
            id=attachment["id"],
            memory_id=attachment["memory_id"],
            blob_key=attachment["blob_key"],
            filename=attachment["filename"],
            mime_type=attachment["mime_type"],
            bytes=attachment["bytes"],
            sha256=attachment["sha256"],
            created_at=attachment["created_at"],
        ),
        "data_base64": data_b64,
    }
