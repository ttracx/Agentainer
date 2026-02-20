"""Embedding service abstraction.

Supports:
- 'stub': deterministic hash-based embeddings for dev/test
- 'openai': OpenAI text-embedding-3-small (or configurable model)
"""

from __future__ import annotations

import hashlib
import struct
from typing import List

import httpx

from .config import Settings


async def embed_text(text: str, settings: Settings) -> List[float]:
    """Generate an embedding vector for the given text."""
    provider = settings.embed_provider

    if provider == "openai":
        return await _embed_openai(text, settings)
    else:
        # Deterministic stub: useful for testing without external API
        return _embed_stub(text, settings.embed_dim)


def _embed_stub(text: str, dim: int) -> List[float]:
    """Deterministic hash-based embedding for dev/test.

    Produces consistent vectors so search tests return predictable results.
    NOT suitable for production retrieval quality.
    """
    digest = hashlib.sha512(text.encode("utf-8")).digest()
    # Repeat the digest bytes to fill the dimension
    expanded = digest * ((dim * 4 // len(digest)) + 1)
    floats = struct.unpack(f"<{dim}f", expanded[: dim * 4])
    # Normalize to unit vector
    magnitude = sum(f * f for f in floats) ** 0.5
    if magnitude == 0:
        return [0.0] * dim
    return [f / magnitude for f in floats]


async def _embed_openai(text: str, settings: Settings) -> List[float]:
    """Call OpenAI embeddings API."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://api.openai.com/v1/embeddings",
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.openai_embed_model,
                "input": text[:8191],  # Model max input tokens safeguard
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["data"][0]["embedding"]
