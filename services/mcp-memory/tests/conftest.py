"""Pytest configuration and fixtures for MCP Memory Server tests."""

from __future__ import annotations

import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Set test environment variables before importing the app
os.environ.setdefault("PG_DSN", "postgresql://memuser:mempass@localhost:5433/memorydb")
os.environ.setdefault("REDIS_URL", "redis://localhost:6380/0")
os.environ.setdefault("EMBED_PROVIDER", "stub")
os.environ.setdefault("EMBED_DIM", "1536")
os.environ.setdefault("BLOB_ENDPOINT_URL", "")
os.environ.setdefault("BLOB_BUCKET", "bellie-blobnlie")
os.environ.setdefault("LOG_LEVEL", "debug")
os.environ.setdefault("MIGRATIONS_DIR", os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "migrations"
))

from app.main import app  # noqa: E402


@pytest_asyncio.fixture
async def client():
    """Provide an async HTTP client against the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
