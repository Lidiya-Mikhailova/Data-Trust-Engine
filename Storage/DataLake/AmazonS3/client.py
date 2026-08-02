from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from Storage.DataLake.AmazonS3.lifecycle import S3Lifecycle
from Storage.DataLake.AmazonS3.reader import S3Reader
from Storage.DataLake.AmazonS3.writer import S3Writer
from Storage.interfaces import DataLakeStorage


class S3Client:
    """Lazy boto3 S3 client wrapper.

    All raw SDK calls are routed through this class so that writer,
    reader and lifecycle modules never import boto3 directly.
    """

    def __init__(self, bucket: str, region: str, prefix: str | None = None) -> None:
        self._bucket = bucket
        self._region = region
        self._prefix = prefix
        self._client: Any = None

    @property
    def bucket(self) -> str:
        return self._bucket

    @property
    def prefix(self) -> str | None:
        return self._prefix

    def _get_client(self) -> Any:
        if self._client is None:
            import boto3  # noqa: WPS433 – lazy import by design

            self._client = boto3.client("s3", region_name=self._region)
        return self._client

    async def put_object(self, key: str, body: bytes) -> None:
        client = self._get_client()
        await asyncio.to_thread(
            client.put_object,
            Bucket=self._bucket,
            Key=key,
            Body=body,
        )

    async def get_object(self, key: str) -> bytes:
        client = self._get_client()
        response = await asyncio.to_thread(
            client.get_object,
            Bucket=self._bucket,
            Key=key,
        )
        return response["Body"].read()  # type: ignore[no-any-return]

    async def head_object(self, key: str) -> bool:
        client = self._get_client()
        try:
            await asyncio.to_thread(
                client.head_object,
                Bucket=self._bucket,
                Key=key,
            )
            return True
        except client.exceptions.ClientError:
            return False

    async def delete_object(self, key: str) -> None:
        client = self._get_client()
        await asyncio.to_thread(
            client.delete_object,
            Bucket=self._bucket,
            Key=key,
        )

    async def list_objects(self, prefix: str) -> list[str]:
        client = self._get_client()
        response = await asyncio.to_thread(
            client.list_objects_v2,
            Bucket=self._bucket,
            Prefix=prefix,
        )
        return [obj["Key"] for obj in response.get("Contents", [])]


class S3DataLake(DataLakeStorage):
    """Amazon S3 implementation of DataLakeStorage.

    Delegates to S3Writer, S3Reader and S3Lifecycle which
    operate through the shared S3Client.
    """

    def __init__(self, bucket: str, region: str, prefix: str | None = None) -> None:
        self._client = S3Client(bucket, region, prefix)
        self._writer = S3Writer(self._client)
        self._reader = S3Reader(self._client)
        self._lifecycle = S3Lifecycle(self._client)

    async def write_raw(self, key: str, data: bytes) -> None:
        await self._writer.write_raw(key, data)

    async def read_raw(self, key: str) -> bytes:
        return await self._reader.read_raw(key)

    async def exists(self, key: str) -> bool:
        return await self._lifecycle.exists(key)

    async def delete(self, key: str) -> None:
        await self._lifecycle.delete(key)

    async def list_raw(self, prefix: str) -> list[str]:
        return await self._reader.list_raw(prefix)

    async def healthcheck(self) -> dict[str, Any]:
        try:
            await self._client.list_objects("")
            status = "healthy"
        except Exception:
            status = "degraded"
        return {"status": status, "timestamp": datetime.now(timezone.utc).isoformat()}
