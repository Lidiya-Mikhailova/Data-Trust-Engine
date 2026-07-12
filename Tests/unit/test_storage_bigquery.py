from __future__ import annotations

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _install_bq_mock():
    mock_bq = MagicMock()
    mock_client_instance = MagicMock()
    mock_client_instance.insert_rows_json.return_value = []
    mock_result = MagicMock()
    mock_result.__iter__ = lambda s: iter({"col": "val"}.items())
    mock_client_instance.query.return_value = mock_result
    mock_client_instance.get_table.return_value = MagicMock()
    mock_bq.Client.return_value = mock_client_instance
    mock_bq.Client.from_service_account_json.return_value = mock_client_instance
    mock_bq.QueryJobConfig.return_value = MagicMock()
    mock_bq.ScalarQueryParameter.return_value = MagicMock()
    mock_bq.Table.return_value = MagicMock()
    mock_bq.SchemaField = MagicMock(side_effect=lambda name, btype: (name, btype))

    mock_cloud = MagicMock()
    mock_cloud.bigquery = mock_bq

    return mock_bq, mock_cloud


def _patch_bq_modules(mock_bq, mock_cloud):
    return patch.dict(sys.modules, {
        "google.cloud.bigquery": mock_bq,
        "google.cloud": mock_cloud,
        "google": MagicMock(),
    })


class TestBigQueryClient:
    @pytest.fixture(autouse=True)
    def _setup(self):
        self._mock_bq, self._mock_cloud = _install_bq_mock()
        self._patcher = _patch_bq_modules(self._mock_bq, self._mock_cloud)
        self._patcher.start()
        yield
        self._patcher.stop()

    def test_properties(self):
        from Storage.Warehouse.GoogleBigQuery.client import BigQueryClient
        client = BigQueryClient("proj", "ds", "/path/to/creds")
        assert client.project_id == "proj"
        assert client.dataset == "ds"

    def test_lazy_client_with_credentials(self):
        from Storage.Warehouse.GoogleBigQuery.client import BigQueryClient
        client = BigQueryClient("proj", "ds", "/path/to/creds")
        assert client._client is None
        bq_client = client._get_client()
        assert bq_client is not None
        self._mock_bq.Client.from_service_account_json.assert_called_once_with(
            "/path/to/creds", project="proj",
        )

    def test_lazy_client_without_credentials(self):
        from Storage.Warehouse.GoogleBigQuery.client import BigQueryClient
        client = BigQueryClient("proj", "ds")
        bq_client = client._get_client()
        assert bq_client is not None
        self._mock_bq.Client.assert_called_once_with(project="proj")

    def test_get_client_reuses(self):
        from Storage.Warehouse.GoogleBigQuery.client import BigQueryClient
        client = BigQueryClient("proj", "ds")
        first = client._get_client()
        second = client._get_client()
        assert first is second

    @pytest.mark.asyncio
    async def test_insert_rows_success(self):
        from Storage.Warehouse.GoogleBigQuery.client import BigQueryClient
        mock_sdk = MagicMock()
        mock_sdk.insert_rows_json.return_value = []
        self._mock_bq.Client.return_value = mock_sdk
        client = BigQueryClient("proj", "ds")
        result = await client.insert_rows("tbl", [{"a": 1}])
        assert result == 1
        mock_sdk.insert_rows_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_insert_rows_raises_on_errors(self):
        from Storage.Warehouse.GoogleBigQuery.client import BigQueryClient
        mock_sdk = MagicMock()
        mock_sdk.insert_rows_json.return_value = [{"error": "fail"}]
        self._mock_bq.Client.return_value = mock_sdk
        client = BigQueryClient("proj", "ds")
        with pytest.raises(ValueError, match="BigQuery insert errors"):
            await client.insert_rows("tbl", [{"a": 1}])

    @pytest.mark.asyncio
    async def test_query_without_params(self):
        from Storage.Warehouse.GoogleBigQuery.client import BigQueryClient
        mock_sdk = MagicMock()
        mock_result = MagicMock()
        mock_result.__iter__ = lambda s: iter([{"col": "val"}])
        mock_sdk.query.return_value = mock_result
        self._mock_bq.Client.return_value = mock_sdk
        self._mock_bq.QueryJobConfig.return_value = MagicMock()
        client = BigQueryClient("proj", "ds")
        result = await client.query("SELECT 1")
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_query_with_params(self):
        from Storage.Warehouse.GoogleBigQuery.client import BigQueryClient
        mock_sdk = MagicMock()
        mock_result = MagicMock()
        mock_result.__iter__ = lambda s: iter([])
        mock_sdk.query.return_value = mock_result
        self._mock_bq.Client.return_value = mock_sdk
        self._mock_bq.QueryJobConfig.return_value = MagicMock()
        self._mock_bq.ScalarQueryParameter.return_value = MagicMock()
        client = BigQueryClient("proj", "ds")
        result = await client.query("SELECT 1", params={"k": "v"})
        assert isinstance(result, list)
        self._mock_bq.ScalarQueryParameter.assert_called_once_with("k", "STRING", "v")

    @pytest.mark.asyncio
    async def test_create_table(self):
        from Storage.Warehouse.GoogleBigQuery.client import BigQueryClient
        mock_sdk = MagicMock()
        self._mock_bq.Client.return_value = mock_sdk
        self._mock_bq.Table.return_value = MagicMock()
        client = BigQueryClient("proj", "ds")
        await client.create_table("tbl", [])
        mock_sdk.create_table.assert_called_once()

    @pytest.mark.asyncio
    async def test_truncate_table(self):
        from Storage.Warehouse.GoogleBigQuery.client import BigQueryClient
        mock_sdk = MagicMock()
        self._mock_bq.Client.return_value = mock_sdk
        client = BigQueryClient("proj", "ds")
        await client.truncate_table("tbl")
        assert mock_sdk.delete_table.call_count == 1
        assert mock_sdk.create_table.call_count == 1

    @pytest.mark.asyncio
    async def test_table_exists_true(self):
        from Storage.Warehouse.GoogleBigQuery.client import BigQueryClient
        mock_sdk = MagicMock()
        mock_sdk.get_table.return_value = MagicMock()
        self._mock_bq.Client.return_value = mock_sdk
        client = BigQueryClient("proj", "ds")
        result = await client.table_exists("tbl")
        assert result is True

    @pytest.mark.asyncio
    async def test_table_exists_false(self):
        from Storage.Warehouse.GoogleBigQuery.client import BigQueryClient
        mock_sdk = MagicMock()
        mock_sdk.get_table.side_effect = Exception("not found")
        self._mock_bq.Client.return_value = mock_sdk
        client = BigQueryClient("proj", "ds")
        result = await client.table_exists("tbl")
        assert result is False


class TestBigQueryWriter:
    @pytest.fixture(autouse=True)
    def _setup(self):
        mock_bq, mock_cloud = _install_bq_mock()
        patcher = _patch_bq_modules(mock_bq, mock_cloud)
        patcher.start()
        yield
        patcher.stop()

    @pytest.mark.asyncio
    async def test_write_gold(self):
        from Storage.Warehouse.GoogleBigQuery.client import BigQueryClient
        from Storage.Warehouse.GoogleBigQuery.writer import BigQueryWriter
        mock_client = MagicMock(spec=BigQueryClient)
        mock_client.insert_rows = AsyncMock(return_value=5)
        writer = BigQueryWriter(mock_client)
        result = await writer.write_gold("tbl", [{"a": 1}], {"a": str})
        assert result == 5
        mock_client.insert_rows.assert_awaited_once_with("tbl", [{"a": 1}])


class TestBigQueryLoader:
    @pytest.fixture(autouse=True)
    def _setup(self):
        mock_bq, mock_cloud = _install_bq_mock()
        patcher = _patch_bq_modules(mock_bq, mock_cloud)
        patcher.start()
        yield
        patcher.stop()

    @pytest.mark.asyncio
    async def test_execute_query(self):
        from Storage.Warehouse.GoogleBigQuery.loader import BigQueryLoader
        mock_client = MagicMock()
        mock_client.query = AsyncMock(return_value=[{"r": 1}])
        loader = BigQueryLoader(mock_client)
        result = await loader.execute_query("SELECT 1")
        assert result == [{"r": 1}]

    @pytest.mark.asyncio
    async def test_create_table(self):
        from Storage.Warehouse.GoogleBigQuery.loader import BigQueryLoader
        mock_client = MagicMock()
        mock_client.create_table = AsyncMock()
        loader = BigQueryLoader(mock_client)
        await loader.create_table("tbl", {"col": str})
        mock_client.create_table.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_truncate(self):
        from Storage.Warehouse.GoogleBigQuery.loader import BigQueryLoader
        mock_client = MagicMock()
        mock_client.truncate_table = AsyncMock()
        loader = BigQueryLoader(mock_client)
        await loader.truncate("tbl")
        mock_client.truncate_table.assert_awaited_once_with("tbl")

    @pytest.mark.asyncio
    async def test_table_exists(self):
        from Storage.Warehouse.GoogleBigQuery.loader import BigQueryLoader
        mock_client = MagicMock()
        mock_client.table_exists = AsyncMock(return_value=True)
        loader = BigQueryLoader(mock_client)
        result = await loader.table_exists("tbl")
        assert result is True


class TestBigQueryWarehouse:
    @pytest.fixture(autouse=True)
    def _setup(self):
        mock_bq, mock_cloud = _install_bq_mock()
        patcher = _patch_bq_modules(mock_bq, mock_cloud)
        patcher.start()
        yield
        patcher.stop()

    @pytest.mark.asyncio
    async def test_write_gold(self):
        from Storage.Warehouse.GoogleBigQuery.client import BigQueryWarehouse
        mock_writer = MagicMock()
        mock_writer.write_gold = AsyncMock(return_value=3)
        mock_loader = MagicMock()
        warehouse = BigQueryWarehouse.__new__(BigQueryWarehouse)
        warehouse._writer = mock_writer
        warehouse._loader = mock_loader
        warehouse._client = MagicMock()
        result = await warehouse.write_gold("tbl", [{"a": 1}], {"a": str})
        assert result == 3

    @pytest.mark.asyncio
    async def test_execute_query(self):
        from Storage.Warehouse.GoogleBigQuery.client import BigQueryWarehouse
        mock_loader = MagicMock()
        mock_loader.execute_query = AsyncMock(return_value=[{"r": 1}])
        mock_writer = MagicMock()
        warehouse = BigQueryWarehouse.__new__(BigQueryWarehouse)
        warehouse._writer = mock_writer
        warehouse._loader = mock_loader
        warehouse._client = MagicMock()
        result = await warehouse.execute_query("SELECT 1")
        assert result == [{"r": 1}]

    @pytest.mark.asyncio
    async def test_create_table(self):
        from Storage.Warehouse.GoogleBigQuery.client import BigQueryWarehouse
        mock_loader = MagicMock()
        mock_loader.create_table = AsyncMock()
        mock_writer = MagicMock()
        warehouse = BigQueryWarehouse.__new__(BigQueryWarehouse)
        warehouse._writer = mock_writer
        warehouse._loader = mock_loader
        warehouse._client = MagicMock()
        await warehouse.create_table("tbl", {"c": str})
        mock_loader.create_table.assert_awaited_once_with("tbl", {"c": str})

    @pytest.mark.asyncio
    async def test_truncate(self):
        from Storage.Warehouse.GoogleBigQuery.client import BigQueryWarehouse
        mock_loader = MagicMock()
        mock_loader.truncate = AsyncMock()
        mock_writer = MagicMock()
        warehouse = BigQueryWarehouse.__new__(BigQueryWarehouse)
        warehouse._writer = mock_writer
        warehouse._loader = mock_loader
        warehouse._client = MagicMock()
        await warehouse.truncate("tbl")
        mock_loader.truncate.assert_awaited_once_with("tbl")

    @pytest.mark.asyncio
    async def test_table_exists(self):
        from Storage.Warehouse.GoogleBigQuery.client import BigQueryWarehouse
        mock_loader = MagicMock()
        mock_loader.table_exists = AsyncMock(return_value=True)
        mock_writer = MagicMock()
        warehouse = BigQueryWarehouse.__new__(BigQueryWarehouse)
        warehouse._writer = mock_writer
        warehouse._loader = mock_loader
        warehouse._client = MagicMock()
        result = await warehouse.table_exists("tbl")
        assert result is True


class TestMapSchema:
    @pytest.fixture(autouse=True)
    def _setup(self):
        mock_bq = MagicMock()
        mock_bq.SchemaField = MagicMock(side_effect=lambda name, btype: (name, btype))
        mock_cloud = MagicMock()
        mock_cloud.bigquery = mock_bq
        patcher = _patch_bq_modules(mock_bq, mock_cloud)
        patcher.start()
        yield
        patcher.stop()

    def test_known_types(self):
        from Storage.Warehouse.GoogleBigQuery.models import _PYTHON_TO_BQ
        assert _PYTHON_TO_BQ[str] == "STRING"
        assert _PYTHON_TO_BQ[int] == "INTEGER"
        assert _PYTHON_TO_BQ[float] == "FLOAT"
        assert _PYTHON_TO_BQ[bool] == "BOOLEAN"
        assert _PYTHON_TO_BQ[bytes] == "BYTES"

    def test_map_schema_known_types(self):
        from Storage.Warehouse.GoogleBigQuery.models import map_schema
        result = map_schema({"name": str, "age": int, "score": float})
        assert len(result) == 3

    def test_map_schema_unknown_type(self):
        from Storage.Warehouse.GoogleBigQuery.models import map_schema
        result = map_schema({"data": dict})
        assert len(result) == 1
        assert result[0] == ("data", "STRING")

    def test_map_schema_empty(self):
        from Storage.Warehouse.GoogleBigQuery.models import map_schema
        result = map_schema({})
        assert result == []
