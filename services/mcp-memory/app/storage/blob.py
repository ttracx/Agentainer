"""Blob store abstraction for bellie-blobnlie (S3-compatible).

Handles uploading/downloading large attachments.
Falls back to local filesystem for dev/test when no S3 endpoint is configured.
"""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
from typing import Optional, Tuple

from ..config import Settings

logger = logging.getLogger("mcp_memory.storage.blob")


class BlobStore:
    """S3-compatible blob store with local filesystem fallback."""

    def __init__(self, settings: Settings):
        self._settings = settings
        self._use_s3 = bool(settings.blob_endpoint_url)
        self._local_dir = Path("/tmp/mcp-memory-blobs")
        self._s3_client = None

    async def initialize(self) -> None:
        if self._use_s3:
            import boto3

            self._s3_client = boto3.client(
                "s3",
                endpoint_url=self._settings.blob_endpoint_url,
                aws_access_key_id=self._settings.blob_access_key,
                aws_secret_access_key=self._settings.blob_secret_key,
                region_name=self._settings.blob_region,
            )
            logger.info(
                "Blob store: S3 at %s bucket=%s",
                self._settings.blob_endpoint_url,
                self._settings.blob_bucket,
            )
        else:
            self._local_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Blob store: local filesystem at %s", self._local_dir)

    async def upload(
        self,
        blob_key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload bytes, return the blob_key."""
        if self._use_s3:
            self._s3_client.put_object(
                Bucket=self._settings.blob_bucket,
                Key=blob_key,
                Body=data,
                ContentType=content_type,
            )
        else:
            dest = self._local_dir / blob_key
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)

        logger.info("Blob uploaded: %s (%d bytes)", blob_key, len(data))
        return blob_key

    async def download(self, blob_key: str) -> Optional[bytes]:
        """Download bytes by blob_key."""
        if self._use_s3:
            try:
                resp = self._s3_client.get_object(
                    Bucket=self._settings.blob_bucket,
                    Key=blob_key,
                )
                return resp["Body"].read()
            except Exception:
                logger.exception("Failed to download blob: %s", blob_key)
                return None
        else:
            path = self._local_dir / blob_key
            if path.exists():
                return path.read_bytes()
            return None

    async def generate_presigned_url(
        self, blob_key: str, expires_in: int = 3600
    ) -> Optional[str]:
        """Generate a presigned download URL (S3 only)."""
        if not self._use_s3:
            return None
        try:
            url = self._s3_client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self._settings.blob_bucket,
                    "Key": blob_key,
                },
                ExpiresIn=expires_in,
            )
            return url
        except Exception:
            logger.exception("Failed to generate presigned URL for: %s", blob_key)
            return None

    @staticmethod
    def compute_sha256(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def make_blob_key(tenant_id: str, memory_id: str, filename: str) -> str:
        """Generate a blob key following tenant/memory/filename structure."""
        safe_filename = filename.replace("/", "_").replace("\\", "_")
        return f"{tenant_id}/{memory_id}/{safe_filename}"
