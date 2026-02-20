# MCP Memory Server

Shared Vector Memory + Knowledge Context server for OpenClaw (Nellie) Gateway and Nodes.

Provides durable, scoped memory persistence and hybrid retrieval (vector similarity + keyword search + metadata filters) via MCP tool endpoints. Nodes never talk directly to databases; they call MCP tools exposed by this service.

## Architecture

```
Gateway / Nodes
      │
      ▼
┌──────────────┐
│  mcp-memory  │ ← FastAPI MCP tool server
│  (port 8000) │
└──────┬───────┘
       │
  ┌────┴─────┐
  │          │
  ▼          ▼
PostgreSQL  Redis
(pgvector)  (cache)
  │
  ▼
bellie-blobnlie
(blob store)
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `memory.write` | Persist a memory entry with vector embedding. Idempotent via content_hash. |
| `memory.search` | Hybrid retrieval: vector + keyword + metadata filters. Strict scope isolation. |
| `memory.get` | Fetch full entry with attachments and links. |
| `memory.link` | Create relationships between entries (supports, derived_from, duplicates, supersedes, related). |
| `memory.summarize_scope` | Create durable scope summaries linked to source entries. |
| `memory.attach_blob` | Upload attachment to blob store + link to memory entry. |
| `memory.fetch_blob` | Retrieve attachment by ID (presigned URL or base64). |

## Memory Types

| Kind | Description |
|------|-------------|
| `chat_turn` | Conversation messages (optional, can be pruned) |
| `task_outcome` | Task completion results with key steps and findings |
| `decision` | Architectural or operational decisions |
| `runbook` | Operational procedures and playbooks |
| `doc_chunk` | Document chunks for RAG-style retrieval |
| `summary` | Auto-generated scope summaries |

## Scoping

All memory operations require `tenant_id` and at least one scope dimension:

```
tenant → channel → conversation → project → task
```

Scope isolation is enforced by default. No cross-scope recall unless explicitly configured.

## Quick Start

### 1. Start the stack

```bash
cd services/mcp-memory
docker compose up -d
```

This starts:
- **mcp-memory** on port 7411 (mapped to internal 8000)
- **PostgreSQL 16 + pgvector** on port 5433
- **Redis 7** on port 6380

Migrations run automatically on startup.

### 2. Verify health

```bash
curl http://localhost:7411/health
# {"status":"ok","postgres":"ok","redis":"ok"}
```

### 3. Write a memory entry

```bash
curl -X POST http://localhost:7411/tools/memory.write \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "t1",
    "scope": {"channel_id": "general", "project_id": "myproject"},
    "kind": "task_outcome",
    "title": "Fixed Docker push timeout",
    "content": "Resolved push stall by increasing client timeout to 300s and verifying layer upload checksums.",
    "tags": ["docker", "infra", "bugfix"],
    "source": "gateway",
    "author_agent_id": "nellie"
  }'
```

### 4. Search memory

```bash
curl -X POST http://localhost:7411/tools/memory.search \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "t1",
    "scope_filter": {"channel_id": "general", "project_id": "myproject"},
    "query": "Docker push timeout",
    "top_k": 5
  }'
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PG_DSN` | (required) | PostgreSQL connection string |
| `REDIS_URL` | (required) | Redis connection string |
| `EMBED_PROVIDER` | `stub` | Embedding provider: `stub` or `openai` |
| `EMBED_DIM` | `1536` | Embedding vector dimension |
| `OPENAI_API_KEY` | | Required if EMBED_PROVIDER=openai |
| `OPENAI_EMBED_MODEL` | `text-embedding-3-small` | OpenAI embedding model |
| `BLOB_ENDPOINT_URL` | | S3-compatible endpoint (empty = local filesystem) |
| `BLOB_BUCKET` | `bellie-blobnlie` | Blob store bucket name |
| `BLOB_ACCESS_KEY` | | S3 access key |
| `BLOB_SECRET_KEY` | | S3 secret key |
| `WORKING_SET_TTL` | `21600` | Redis working set TTL (seconds, default 6h) |
| `WORKING_SET_MAX` | `50` | Max items in Redis working set |
| `SEARCH_CACHE_TTL` | `600` | Search result cache TTL (seconds, default 10min) |
| `LOG_LEVEL` | `info` | Logging level |

## Running Tests

```bash
# Start backing services
docker compose up -d postgres redis

# Install test dependencies
pip install -r requirements-test.txt

# Run tests
cd services/mcp-memory
pytest tests/ -v --tb=short
```

## Health Checks

- **HTTP**: `GET /health` returns `{"status": "ok", "postgres": "ok", "redis": "ok"}`
- **Docker**: Built-in healthcheck every 15s
- **Stats**: `GET /stats/{tenant_id}` returns write/search/cache counters

## Common Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `health` returns `postgres: error` | PG not reachable | Check PG_DSN, verify postgres container is running |
| `health` returns `redis: error` | Redis not reachable | Check REDIS_URL, verify redis container is running |
| Search returns empty | No entries in scope | Write entries first; check scope parameters match |
| Duplicate write returns same ID | Content hash dedupe | Expected behavior; `updated_at` is refreshed |
| Blob upload fails | Missing BLOB_ENDPOINT_URL | Use local fallback (leave empty) or configure S3 |
| Embedding quality poor | Using `stub` provider | Switch to `openai` or another real embedding provider |
| Migration fails on startup | Missing pgvector extension | Use `pgvector/pgvector:pg16` Docker image |

## Gateway Integration

The server includes Gateway hooks for automatic memory writes:

- **on_message_received**: Writes `chat_turn` entries (optional)
- **on_task_completed**: Writes `task_outcome` entries (always)
- **on_tool_completed**: Writes tool results as `task_outcome`

And a **preflight** module for node context bootstrap:

```python
from app.gateway.preflight import PreflightContext

preflight = PreflightContext(pg, cache, settings)
context = await preflight.get_context(
    tenant_id="t1",
    scope={"channel_id": "general", "project_id": "myproject"},
    task_title="Fix Docker build failure",
)
# context["known_context"] -> formatted string for agent prompt injection
```

## Scheduled Jobs

| Job | Module | Purpose |
|-----|--------|---------|
| Summarize | `app.jobs.summarize` | Weekly scope summaries |
| Promote | `app.jobs.promote` | Tag frequently-referenced entries as `promoted` |
| Prune | `app.jobs.prune` | Delete old `chat_turn` entries (not promoted) |

These can be triggered via cron, Celery, or any scheduler.
