"""Pydantic models for MCP Memory Server request/response contracts."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ── Scope ────────────────────────────────────────────────────────────

class ScopeIn(BaseModel):
    """Hierarchical scope for memory isolation."""
    channel_id: Optional[str] = None
    conversation_id: Optional[str] = None
    project_id: Optional[str] = None
    task_id: Optional[str] = None


# ── memory.write ─────────────────────────────────────────────────────

class MemoryWriteIn(BaseModel):
    """Input for memory.write tool."""
    tenant_id: str
    scope: ScopeIn
    kind: str = Field(
        ...,
        description="chat_turn | task_outcome | decision | runbook | doc_chunk | summary",
    )
    title: Optional[str] = None
    content: str
    tags: List[str] = Field(default_factory=list)
    source: Optional[str] = "gateway"
    author_agent_id: Optional[str] = None
    tool_name: Optional[str] = None


class MemoryOut(BaseModel):
    """Standard memory entry output."""
    id: str
    kind: str
    title: Optional[str]
    content: str
    tags: List[str]
    source: Optional[str] = None
    author_agent_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    score: Optional[float] = None


# ── memory.search ────────────────────────────────────────────────────

class MemorySearchIn(BaseModel):
    """Input for memory.search tool."""
    tenant_id: str
    scope_filter: ScopeIn
    query: str
    top_k: int = Field(default=10, ge=1, le=100)
    tags: List[str] = Field(default_factory=list)
    kinds: List[str] = Field(default_factory=list)
    time_range_start: Optional[datetime] = None
    time_range_end: Optional[datetime] = None


# ── memory.get ───────────────────────────────────────────────────────

class MemoryGetIn(BaseModel):
    """Input for memory.get tool."""
    tenant_id: str
    memory_id: str


class MemoryGetOut(BaseModel):
    """Full memory entry with attachments and links."""
    entry: MemoryOut
    attachments: List[AttachmentOut] = Field(default_factory=list)
    linked_from: List[LinkOut] = Field(default_factory=list)
    linked_to: List[LinkOut] = Field(default_factory=list)


# ── memory.link ──────────────────────────────────────────────────────

class MemoryLinkIn(BaseModel):
    """Input for memory.link tool."""
    tenant_id: str
    from_memory_id: str
    to_memory_id: str
    relation: str = Field(
        ...,
        description="supports | derived_from | duplicates | supersedes | related",
    )


class LinkOut(BaseModel):
    """A relationship between two memory entries."""
    id: int
    from_memory_id: str
    to_memory_id: str
    relation: str
    created_at: datetime


# ── memory.summarize_scope ───────────────────────────────────────────

class SummarizeScopeIn(BaseModel):
    """Input for memory.summarize_scope tool."""
    tenant_id: str
    scope: ScopeIn
    mode: str = Field(default="brief", description="brief | full")
    max_entries: int = Field(default=50, ge=1, le=500)


# ── memory.attach_blob / fetch_blob ─────────────────────────────────

class AttachBlobIn(BaseModel):
    """Input for memory.attach_blob tool."""
    tenant_id: str
    memory_id: str
    filename: str
    mime_type: str
    data_base64: str


class FetchBlobIn(BaseModel):
    """Input for memory.fetch_blob tool."""
    tenant_id: str
    attachment_id: str


class AttachmentOut(BaseModel):
    """Attachment metadata output."""
    id: str
    memory_id: str
    blob_key: str
    filename: str
    mime_type: str
    bytes: int
    sha256: str
    created_at: datetime
    download_url: Optional[str] = None


# Forward reference resolution
MemoryGetOut.model_rebuild()
