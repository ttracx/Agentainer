"""End-to-end tests for the MCP Memory Server.

Tests the core flow: write -> search -> get -> link -> summarize -> attach/fetch.

Requirements:
- PostgreSQL running with pgvector extension (docker-compose up postgres)
- Redis running (docker-compose up redis)
- Migrations applied (server auto-applies on startup)

Run: pytest tests/ -v --tb=short
"""

from __future__ import annotations

import base64

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

TENANT = "test-tenant"
SCOPE = {"channel_id": "ch-test", "conversation_id": "conv-test"}


class TestHealthCheck:
    """Health endpoint should report backend status."""

    async def test_health(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["postgres"] == "ok"
        assert data["redis"] == "ok"


class TestMemoryWrite:
    """memory.write should persist entries with dedupe."""

    async def test_write_task_outcome(self, client: AsyncClient):
        payload = {
            "tenant_id": TENANT,
            "scope": SCOPE,
            "kind": "task_outcome",
            "title": "docker push fix",
            "content": "Resolved push stall by increasing client timeout and verifying layer upload.",
            "tags": ["docker", "infra"],
            "source": "gateway",
            "author_agent_id": "nellie",
        }
        resp = await client.post("/tools/memory.write", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"].startswith("mem_")
        assert data["kind"] == "task_outcome"
        assert data["title"] == "docker push fix"
        assert "docker" in data["tags"]

    async def test_write_dedupe(self, client: AsyncClient):
        """Writing the same content twice should not create duplicates."""
        payload = {
            "tenant_id": TENANT,
            "scope": SCOPE,
            "kind": "decision",
            "title": "use pgvector",
            "content": "Decided to use pgvector for embeddings storage over a standalone vector DB.",
            "tags": ["architecture"],
            "source": "gateway",
        }
        r1 = await client.post("/tools/memory.write", json=payload)
        r2 = await client.post("/tools/memory.write", json=payload)
        assert r1.status_code == 200
        assert r2.status_code == 200
        # Same ID means dedupe worked
        assert r1.json()["id"] == r2.json()["id"]

    async def test_write_chat_turn(self, client: AsyncClient):
        payload = {
            "tenant_id": TENANT,
            "scope": SCOPE,
            "kind": "chat_turn",
            "content": "Can you help me fix the Docker build failure?",
            "source": "gateway",
            "author_agent_id": "user-1",
        }
        resp = await client.post("/tools/memory.write", json=payload)
        assert resp.status_code == 200


class TestMemorySearch:
    """memory.search should return relevant results via hybrid retrieval."""

    async def test_search_finds_written_entry(self, client: AsyncClient):
        # Write an entry first
        await client.post("/tools/memory.write", json={
            "tenant_id": TENANT,
            "scope": SCOPE,
            "kind": "task_outcome",
            "title": "playwright headless fix",
            "content": "Fixed Playwright headless Chrome by installing missing system dependencies.",
            "tags": ["playwright", "testing"],
            "source": "gateway",
            "author_agent_id": "coder-1",
        })

        # Search for it
        resp = await client.post("/tools/memory.search", json={
            "tenant_id": TENANT,
            "scope_filter": SCOPE,
            "query": "playwright headless Chrome dependencies",
            "top_k": 5,
        })
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) >= 1

    async def test_search_with_tag_filter(self, client: AsyncClient):
        resp = await client.post("/tools/memory.search", json={
            "tenant_id": TENANT,
            "scope_filter": SCOPE,
            "query": "docker",
            "top_k": 10,
            "tags": ["docker"],
        })
        assert resp.status_code == 200
        results = resp.json()
        # All results should have the 'docker' tag
        for r in results:
            assert "docker" in r["tags"]

    async def test_search_with_kind_filter(self, client: AsyncClient):
        resp = await client.post("/tools/memory.search", json={
            "tenant_id": TENANT,
            "scope_filter": SCOPE,
            "query": "fix",
            "top_k": 10,
            "kinds": ["task_outcome"],
        })
        assert resp.status_code == 200
        results = resp.json()
        for r in results:
            assert r["kind"] == "task_outcome"

    async def test_search_scope_isolation(self, client: AsyncClient):
        """Entries from one scope should not appear in another scope's search."""
        other_scope = {"channel_id": "ch-other", "conversation_id": "conv-other"}

        # Write to the other scope
        await client.post("/tools/memory.write", json={
            "tenant_id": TENANT,
            "scope": other_scope,
            "kind": "task_outcome",
            "title": "secret project result",
            "content": "This should not appear in ch-test searches.",
            "tags": ["secret"],
            "source": "gateway",
        })

        # Search in the original scope
        resp = await client.post("/tools/memory.search", json={
            "tenant_id": TENANT,
            "scope_filter": SCOPE,
            "query": "secret project result",
            "top_k": 10,
        })
        results = resp.json()
        for r in results:
            assert r["title"] != "secret project result"


class TestMemoryGet:
    """memory.get should return full entry with attachments and links."""

    async def test_get_entry(self, client: AsyncClient):
        # Write first
        w = await client.post("/tools/memory.write", json={
            "tenant_id": TENANT,
            "scope": SCOPE,
            "kind": "runbook",
            "title": "deploy process",
            "content": "Step 1: Build image. Step 2: Push to registry. Step 3: Deploy to k8s.",
            "tags": ["deploy", "runbook"],
            "source": "gateway",
        })
        mem_id = w.json()["id"]

        # Get it
        resp = await client.post("/tools/memory.get", json={
            "tenant_id": TENANT,
            "memory_id": mem_id,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["entry"]["id"] == mem_id
        assert data["entry"]["kind"] == "runbook"
        assert isinstance(data["attachments"], list)
        assert isinstance(data["linked_from"], list)
        assert isinstance(data["linked_to"], list)

    async def test_get_nonexistent(self, client: AsyncClient):
        resp = await client.post("/tools/memory.get", json={
            "tenant_id": TENANT,
            "memory_id": "mem_doesnotexist",
        })
        assert resp.status_code == 404


class TestMemoryLink:
    """memory.link should create relationships between entries."""

    async def test_link_entries(self, client: AsyncClient):
        # Write two entries
        r1 = await client.post("/tools/memory.write", json={
            "tenant_id": TENANT,
            "scope": SCOPE,
            "kind": "task_outcome",
            "title": "original finding",
            "content": "Discovered that the API rate limit is 100 req/min.",
            "tags": ["api"],
            "source": "gateway",
        })
        r2 = await client.post("/tools/memory.write", json={
            "tenant_id": TENANT,
            "scope": SCOPE,
            "kind": "decision",
            "title": "implement rate limiter",
            "content": "Based on the API rate limit finding, implementing a client-side rate limiter.",
            "tags": ["api", "architecture"],
            "source": "gateway",
        })

        id1 = r1.json()["id"]
        id2 = r2.json()["id"]

        # Link them
        resp = await client.post("/tools/memory.link", json={
            "tenant_id": TENANT,
            "from_memory_id": id2,
            "to_memory_id": id1,
            "relation": "derived_from",
        })
        assert resp.status_code == 200
        link = resp.json()
        assert link["relation"] == "derived_from"

        # Verify via get
        get_resp = await client.post("/tools/memory.get", json={
            "tenant_id": TENANT,
            "memory_id": id2,
        })
        data = get_resp.json()
        assert len(data["linked_from"]) >= 1


class TestSummarizeScope:
    """memory.summarize_scope should create a summary entry linked to sources."""

    async def test_summarize(self, client: AsyncClient):
        # Ensure there are entries to summarize
        for i in range(3):
            await client.post("/tools/memory.write", json={
                "tenant_id": TENANT,
                "scope": SCOPE,
                "kind": "task_outcome",
                "title": f"task result {i}",
                "content": f"Completed task {i} with specific results and findings number {i}.",
                "tags": ["test"],
                "source": "gateway",
            })

        resp = await client.post("/tools/memory.summarize_scope", json={
            "tenant_id": TENANT,
            "scope": SCOPE,
            "mode": "brief",
            "max_entries": 20,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["kind"] == "summary"
        assert "auto_summary" in data["tags"]


class TestBlobAttachment:
    """memory.attach_blob and memory.fetch_blob should handle file attachments."""

    async def test_attach_and_fetch(self, client: AsyncClient):
        # Write a memory entry first
        w = await client.post("/tools/memory.write", json={
            "tenant_id": TENANT,
            "scope": SCOPE,
            "kind": "doc_chunk",
            "title": "deployment log",
            "content": "Full deployment log from 2024-01-15 production release.",
            "tags": ["deploy", "log"],
            "source": "gateway",
        })
        mem_id = w.json()["id"]

        # Attach a blob
        test_data = b"This is a test deployment log file content."
        data_b64 = base64.b64encode(test_data).decode()

        attach_resp = await client.post("/tools/memory.attach_blob", json={
            "tenant_id": TENANT,
            "memory_id": mem_id,
            "filename": "deploy-2024-01-15.log",
            "mime_type": "text/plain",
            "data_base64": data_b64,
        })
        assert attach_resp.status_code == 200
        attachment = attach_resp.json()
        assert attachment["filename"] == "deploy-2024-01-15.log"
        assert attachment["bytes"] == len(test_data)

        # Fetch the blob
        fetch_resp = await client.post("/tools/memory.fetch_blob", json={
            "tenant_id": TENANT,
            "attachment_id": attachment["id"],
        })
        assert fetch_resp.status_code == 200
        fetch_data = fetch_resp.json()
        assert fetch_data["data_base64"] is not None
        # Verify content roundtrip
        decoded = base64.b64decode(fetch_data["data_base64"])
        assert decoded == test_data


class TestStats:
    """Stats endpoint should return observability counters."""

    async def test_stats(self, client: AsyncClient):
        resp = await client.get(f"/stats/{TENANT}")
        assert resp.status_code == 200
        data = resp.json()
        assert "writes" in data
        assert "searches" in data
