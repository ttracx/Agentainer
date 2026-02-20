"""MCP Memory Server configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    """Server settings loaded from environment variables."""

    # PostgreSQL
    pg_dsn: str = field(
        default_factory=lambda: os.environ.get(
            "PG_DSN", "postgresql://user:pass@localhost:5432/vibedb"
        )
    )
    pg_min_pool: int = int(os.environ.get("PG_MIN_POOL", "2"))
    pg_max_pool: int = int(os.environ.get("PG_MAX_POOL", "20"))

    # Redis
    redis_url: str = field(
        default_factory=lambda: os.environ.get(
            "REDIS_URL", "redis://localhost:6379/0"
        )
    )

    # Embeddings
    embed_dim: int = int(os.environ.get("EMBED_DIM", "1536"))
    embed_provider: str = os.environ.get("EMBED_PROVIDER", "stub")
    # If using OpenAI embeddings:
    openai_api_key: str = os.environ.get("OPENAI_API_KEY", "")
    openai_embed_model: str = os.environ.get(
        "OPENAI_EMBED_MODEL", "text-embedding-3-small"
    )

    # Blob store (S3-compatible / bellie-blobnlie)
    blob_endpoint_url: str = os.environ.get("BLOB_ENDPOINT_URL", "")
    blob_bucket: str = os.environ.get("BLOB_BUCKET", "bellie-blobnlie")
    blob_access_key: str = os.environ.get("BLOB_ACCESS_KEY", "")
    blob_secret_key: str = os.environ.get("BLOB_SECRET_KEY", "")
    blob_region: str = os.environ.get("BLOB_REGION", "us-east-1")

    # Redis cache TTLs (seconds)
    working_set_ttl: int = int(os.environ.get("WORKING_SET_TTL", str(6 * 3600)))
    working_set_max: int = int(os.environ.get("WORKING_SET_MAX", "50"))
    search_cache_ttl: int = int(os.environ.get("SEARCH_CACHE_TTL", str(10 * 60)))

    # Server
    host: str = os.environ.get("HOST", "0.0.0.0")
    port: int = int(os.environ.get("PORT", "8000"))
    log_level: str = os.environ.get("LOG_LEVEL", "info")

    # Migrations
    migrations_dir: str = os.environ.get(
        "MIGRATIONS_DIR", "/app/migrations"
    )


def get_settings() -> Settings:
    """Return a Settings instance (cached at module level)."""
    return Settings()
