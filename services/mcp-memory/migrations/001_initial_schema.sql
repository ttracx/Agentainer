-- MCP Memory Server: Initial Schema
-- Requires PostgreSQL 16+ with pgvector and pg_trgm extensions

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ============================================================
-- Tenants
-- ============================================================
CREATE TABLE IF NOT EXISTS tenants (
    id   TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- Scopes (strict hierarchical isolation)
-- tenant -> channel -> conversation -> project -> task
-- ============================================================
CREATE TABLE IF NOT EXISTS scopes (
    id              TEXT PRIMARY KEY,
    tenant_id       TEXT NOT NULL REFERENCES tenants(id),
    channel_id      TEXT,
    conversation_id TEXT,
    project_id      TEXT,
    task_id         TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_scopes_tenant
    ON scopes (tenant_id);

-- ============================================================
-- Memory Entries (durable knowledge store)
-- ============================================================
CREATE TABLE IF NOT EXISTS memory_entries (
    id              TEXT PRIMARY KEY,
    tenant_id       TEXT NOT NULL REFERENCES tenants(id),
    scope_id        TEXT NOT NULL REFERENCES scopes(id),

    kind            TEXT NOT NULL,  -- chat_turn | task_outcome | decision | runbook | doc_chunk | summary
    title           TEXT,
    content         TEXT NOT NULL,

    -- governance / retrieval metadata
    tags            TEXT[] NOT NULL DEFAULT '{}',
    source          TEXT,            -- gateway | node | import | system
    author_agent_id TEXT,            -- nellie | coder-1 etc.
    tool_name       TEXT,            -- browser_use | computer_use etc.

    -- dedupe / idempotency
    content_hash    TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Dedupe constraint: no duplicate content per tenant+scope+kind
ALTER TABLE memory_entries
    ADD CONSTRAINT uq_memory_dedupe
    UNIQUE (tenant_id, scope_id, kind, content_hash);

-- Composite index for scoped time-ordered queries
CREATE INDEX IF NOT EXISTS idx_memory_entries_tenant_scope_created
    ON memory_entries (tenant_id, scope_id, created_at DESC);

-- GIN index for tag-based filtering
CREATE INDEX IF NOT EXISTS idx_memory_entries_tags
    ON memory_entries USING GIN (tags);

-- Trigram index for keyword/fuzzy search on content
CREATE INDEX IF NOT EXISTS idx_memory_entries_content_trgm
    ON memory_entries USING GIN (content gin_trgm_ops);

-- Trigram index for keyword search on title
CREATE INDEX IF NOT EXISTS idx_memory_entries_title_trgm
    ON memory_entries USING GIN (title gin_trgm_ops);

-- Kind index for filtered queries
CREATE INDEX IF NOT EXISTS idx_memory_entries_kind
    ON memory_entries (kind);

-- ============================================================
-- Memory Embeddings (pgvector)
-- ============================================================
CREATE TABLE IF NOT EXISTS memory_embeddings (
    memory_id TEXT PRIMARY KEY REFERENCES memory_entries(id) ON DELETE CASCADE,
    embedding vector(1536) NOT NULL
);

-- IVFFlat index for approximate nearest-neighbor search
-- Note: requires at least ~1000 rows to be effective; falls back to sequential scan otherwise
CREATE INDEX IF NOT EXISTS idx_memory_embeddings_ivf
    ON memory_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================================
-- Memory Links (relationships between entries)
-- ============================================================
CREATE TABLE IF NOT EXISTS memory_links (
    id              BIGSERIAL PRIMARY KEY,
    tenant_id       TEXT NOT NULL REFERENCES tenants(id),
    from_memory_id  TEXT NOT NULL REFERENCES memory_entries(id) ON DELETE CASCADE,
    to_memory_id    TEXT NOT NULL REFERENCES memory_entries(id) ON DELETE CASCADE,
    relation        TEXT NOT NULL,  -- supports | derived_from | duplicates | supersedes | related
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_memory_link UNIQUE (from_memory_id, to_memory_id, relation)
);

CREATE INDEX IF NOT EXISTS idx_memory_links_from
    ON memory_links (from_memory_id);

CREATE INDEX IF NOT EXISTS idx_memory_links_to
    ON memory_links (to_memory_id);

-- ============================================================
-- Memory Attachments (pointers to blob store)
-- ============================================================
CREATE TABLE IF NOT EXISTS memory_attachments (
    id          TEXT PRIMARY KEY,
    tenant_id   TEXT NOT NULL REFERENCES tenants(id),
    memory_id   TEXT NOT NULL REFERENCES memory_entries(id) ON DELETE CASCADE,
    blob_key    TEXT NOT NULL,       -- key/path in bellie-blobnlie
    filename    TEXT NOT NULL,
    mime_type   TEXT NOT NULL,
    bytes       BIGINT NOT NULL,
    sha256      TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_memory_attachments_memory
    ON memory_attachments (memory_id);

-- ============================================================
-- ACL Stubs (deny-by-default policy, expand later)
-- ============================================================
CREATE TABLE IF NOT EXISTS memory_acl (
    id          BIGSERIAL PRIMARY KEY,
    tenant_id   TEXT NOT NULL REFERENCES tenants(id),
    scope_id    TEXT NOT NULL REFERENCES scopes(id),
    principal   TEXT NOT NULL,       -- agent_id or role
    permission  TEXT NOT NULL DEFAULT 'read',  -- read | write | admin
    granted     BOOLEAN NOT NULL DEFAULT false,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_memory_acl_scope
    ON memory_acl (tenant_id, scope_id, principal);
