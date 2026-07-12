from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Storage.DataLake.AmazonS3.client import S3Client


class S3Writer:
    """Handles all write operations for S3 Data Lake."""

    def __init__(self, client: S3Client) -> None:
        self._client = client

    async def write_raw(self, key: str, data: bytes) -> None:
        await self._client.put_object(key, data)
