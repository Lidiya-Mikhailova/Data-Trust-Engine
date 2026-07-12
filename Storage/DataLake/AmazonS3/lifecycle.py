from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Storage.DataLake.AmazonS3.client import S3Client


class S3Lifecycle:
    """Handles lifecycle operations (existence checks, deletion) for S3 Data Lake."""

    def __init__(self, client: S3Client) -> None:
        self._client = client

    async def exists(self, key: str) -> bool:
        return await self._client.head_object(key)

    async def delete(self, key: str) -> None:
        await self._client.delete_object(key)
