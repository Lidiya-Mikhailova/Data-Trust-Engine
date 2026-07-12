from __future__ import annotations

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from Storage.DataLake.AmazonS3.client import S3Client, S3DataLake
from Storage.DataLake.AmazonS3.lifecycle import S3Lifecycle
from Storage.DataLake.AmazonS3.reader import S3Reader
from Storage.DataLake.AmazonS3.writer import S3Writer


def _make_mock_boto3():
    mock_boto3 = MagicMock()
    mock_sdk = MagicMock()
    mock_sdk.put_object = MagicMock()
    mock_sdk.get_object = MagicMock(return_value={"Body": MagicMock(read=MagicMock(return_value=b"data"))})
    mock_sdk.head_object = MagicMock()
    mock_sdk.delete_object = MagicMock()
    mock_sdk.list_objects_v2 = MagicMock(return_value={"Contents": [{"Key": "a/b/c"}, {"Key": "a/b/d"}]})
    mock_sdk.exceptions.ClientError = type("ClientError", (Exception,), {})
    mock_boto3.client.return_value = mock_sdk
    return mock_boto3, mock_sdk


class TestS3Client:
    def test_properties(self):
        client = S3Client("my-bucket", "us-east-1", prefix="raw/")
        assert client.bucket == "my-bucket"
        assert client.prefix == "raw/"

    def test_properties_no_prefix(self):
        client = S3Client("my-bucket", "us-east-1")
        assert client.prefix is None

    def test_lazy_get_client(self):
        mock_boto3, mock_sdk = _make_mock_boto3()
        with patch.dict(sys.modules, {"boto3": mock_boto3}):
            client = S3Client("bucket", "us-east-1")
            assert client._client is None
            first = client._get_client()
            second = client._get_client()
            assert first is second
            mock_boto3.client.assert_called_once_with("s3", region_name="us-east-1")

    @pytest.mark.asyncio
    async def test_put_object(self):
        mock_boto3, mock_sdk = _make_mock_boto3()
        with patch.dict(sys.modules, {"boto3": mock_boto3}):
            client = S3Client("bucket", "us-east-1")
            await client.put_object("key1", b"body1")
            mock_sdk.put_object.assert_called_once_with(
                Bucket="bucket", Key="key1", Body=b"body1",
            )

    @pytest.mark.asyncio
    async def test_get_object(self):
        mock_boto3, mock_sdk = _make_mock_boto3()
        with patch.dict(sys.modules, {"boto3": mock_boto3}):
            client = S3Client("bucket", "us-east-1")
            result = await client.get_object("key1")
            assert result == b"data"
            mock_sdk.get_object.assert_called_once_with(Bucket="bucket", Key="key1")

    @pytest.mark.asyncio
    async def test_head_object_exists(self):
        mock_boto3, mock_sdk = _make_mock_boto3()
        with patch.dict(sys.modules, {"boto3": mock_boto3}):
            client = S3Client("bucket", "us-east-1")
            result = await client.head_object("key1")
            assert result is True

    @pytest.mark.asyncio
    async def test_head_object_not_found(self):
        mock_boto3, mock_sdk = _make_mock_boto3()
        mock_sdk.head_object.side_effect = mock_sdk.exceptions.ClientError()
        with patch.dict(sys.modules, {"boto3": mock_boto3}):
            client = S3Client("bucket", "us-east-1")
            result = await client.head_object("missing")
            assert result is False

    @pytest.mark.asyncio
    async def test_delete_object(self):
        mock_boto3, mock_sdk = _make_mock_boto3()
        with patch.dict(sys.modules, {"boto3": mock_boto3}):
            client = S3Client("bucket", "us-east-1")
            await client.delete_object("key1")
            mock_sdk.delete_object.assert_called_once_with(Bucket="bucket", Key="key1")

    @pytest.mark.asyncio
    async def test_list_objects(self):
        mock_boto3, mock_sdk = _make_mock_boto3()
        with patch.dict(sys.modules, {"boto3": mock_boto3}):
            client = S3Client("bucket", "us-east-1")
            result = await client.list_objects("a/")
            assert result == ["a/b/c", "a/b/d"]
            mock_sdk.list_objects_v2.assert_called_once_with(Bucket="bucket", Prefix="a/")

    @pytest.mark.asyncio
    async def test_list_objects_empty(self):
        mock_boto3, mock_sdk = _make_mock_boto3()
        mock_sdk.list_objects_v2.return_value = {}
        with patch.dict(sys.modules, {"boto3": mock_boto3}):
            client = S3Client("bucket", "us-east-1")
            result = await client.list_objects("empty/")
            assert result == []


class TestS3Writer:
    @pytest.mark.asyncio
    async def test_write_raw(self):
        mock_client = MagicMock()
        mock_client.put_object = AsyncMock()
        writer = S3Writer(mock_client)
        await writer.write_raw("k", b"d")
        mock_client.put_object.assert_awaited_once_with("k", b"d")


class TestS3Reader:
    @pytest.mark.asyncio
    async def test_read_raw(self):
        mock_client = MagicMock()
        mock_client.get_object = AsyncMock(return_value=b"payload")
        reader = S3Reader(mock_client)
        result = await reader.read_raw("k")
        assert result == b"payload"

    @pytest.mark.asyncio
    async def test_list_raw(self):
        mock_client = MagicMock()
        mock_client.list_objects = AsyncMock(return_value=["a", "b"])
        reader = S3Reader(mock_client)
        result = await reader.list_raw("p/")
        assert result == ["a", "b"]


class TestS3Lifecycle:
    @pytest.mark.asyncio
    async def test_exists(self):
        mock_client = MagicMock()
        mock_client.head_object = AsyncMock(return_value=True)
        lifecycle = S3Lifecycle(mock_client)
        result = await lifecycle.exists("k")
        assert result is True
        mock_client.head_object.assert_awaited_once_with("k")

    @pytest.mark.asyncio
    async def test_delete(self):
        mock_client = MagicMock()
        mock_client.delete_object = AsyncMock()
        lifecycle = S3Lifecycle(mock_client)
        await lifecycle.delete("k")
        mock_client.delete_object.assert_awaited_once_with("k")


class TestS3DataLake:
    @pytest.mark.asyncio
    async def test_write_raw(self):
        mock_boto3, mock_sdk = _make_mock_boto3()
        with patch.dict(sys.modules, {"boto3": mock_boto3}):
            lake = S3DataLake("bucket", "us-east-1")
            await lake.write_raw("k", b"d")
            mock_sdk.put_object.assert_called_once_with(Bucket="bucket", Key="k", Body=b"d")

    @pytest.mark.asyncio
    async def test_read_raw(self):
        mock_boto3, mock_sdk = _make_mock_boto3()
        with patch.dict(sys.modules, {"boto3": mock_boto3}):
            lake = S3DataLake("bucket", "us-east-1")
            result = await lake.read_raw("k")
            assert result == b"data"

    @pytest.mark.asyncio
    async def test_exists(self):
        mock_boto3, mock_sdk = _make_mock_boto3()
        with patch.dict(sys.modules, {"boto3": mock_boto3}):
            lake = S3DataLake("bucket", "us-east-1")
            result = await lake.exists("k")
            assert result is True

    @pytest.mark.asyncio
    async def test_delete(self):
        mock_boto3, mock_sdk = _make_mock_boto3()
        with patch.dict(sys.modules, {"boto3": mock_boto3}):
            lake = S3DataLake("bucket", "us-east-1")
            await lake.delete("k")
            mock_sdk.delete_object.assert_called_once_with(Bucket="bucket", Key="k")

    @pytest.mark.asyncio
    async def test_list_raw(self):
        mock_boto3, mock_sdk = _make_mock_boto3()
        with patch.dict(sys.modules, {"boto3": mock_boto3}):
            lake = S3DataLake("bucket", "us-east-1")
            result = await lake.list_raw("a/")
            assert result == ["a/b/c", "a/b/d"]
