from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Storage.DataLake.AmazonS3.client import S3Client


class S3Reader:
    """Handles all read operations for S3 Data Lake."""

    def __init__(self, client: S3Client) -> None:
        self._client = client

    async def read_raw(self, key: str) -> bytes:
        return await self._client.get_object(key)

    async def list_raw(self, prefix: str) -> list[str]:
        return await self._client.list_objects(prefix)
