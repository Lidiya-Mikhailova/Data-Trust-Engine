from __future__ import annotations

import asyncio
from typing import Any

from Storage.Warehouse.GoogleBigQuery.loader import BigQueryLoader
from Storage.Warehouse.GoogleBigQuery.writer import BigQueryWriter
from Storage.interfaces import WarehouseStorage


class BigQueryClient:
    """Lazy google-cloud-bigquery client wrapper.

    All raw SDK calls are routed through this class so that writer
    and loader modules never import google.cloud.bigquery directly.
    """

    def __init__(
        self,
        project_id: str,
        dataset: str,
        credentials_path: str | None = None,
    ) -> None:
        self._project_id = project_id
        self._dataset = dataset
        self._credentials_path = credentials_path
        self._client: Any = None

    @property
    def project_id(self) -> str:
        return self._project_id

    @property
    def dataset(self) -> str:
        return self._dataset

    def _get_client(self) -> Any:
        if self._client is None:
            from google.cloud import bigquery  # noqa: WPS433 – lazy import by design

            if self._credentials_path:
                self._client = bigquery.Client.from_service_account_json(
                    self._credentials_path,
                    project=self._project_id,
                )
            else:
                self._client = bigquery.Client(project=self._project_id)
        return self._client

    async def insert_rows(
        self,
        table: str,
        rows: list[dict[str, Any]],
    ) -> int:
        client = self._get_client()
        table_ref = f"{self._project_id}.{self._dataset}.{table}"
        errors = await asyncio.to_thread(
            client.insert_rows_json,
            table_ref,
            rows,
        )
        if errors:
            raise ValueError(f"BigQuery insert errors: {errors}")
        return len(rows)

    async def query(
        self,
        sql: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        from google.cloud import bigquery  # noqa: WPS433

        client = self._get_client()
        job_config = bigquery.QueryJobConfig()
        if params:
            job_config.query_parameters = [
                bigquery.ScalarQueryParameter(k, "STRING", v)
                for k, v in params.items()
            ]
        result = await asyncio.to_thread(
            client.query,
            sql,
            job_config,
        )
        return [dict(row) for row in result]

    async def create_table(self, table: str, schema: list[Any]) -> None:
        from google.cloud import bigquery  # noqa: WPS433

        client = self._get_client()
        table_ref = f"{self._project_id}.{self._dataset}.{table}"
        bq_table = bigquery.Table(table_ref, schema=schema)
        bq_table.time_partitioning = None
        await asyncio.to_thread(client.create_table, bq_table, exists_ok=True)

    async def truncate_table(self, table: str) -> None:
        client = self._get_client()
        table_ref = f"{self._project_id}.{self._dataset}.{table}"
        await asyncio.to_thread(
            client.delete_table,
            table_ref,
        )
        await asyncio.to_thread(
            client.create_table,
            table_ref,
        )

    async def table_exists(self, table: str) -> bool:
        client = self._get_client()
        table_ref = f"{self._project_id}.{self._dataset}.{table}"
        try:
            await asyncio.to_thread(client.get_table, table_ref)
            return True
        except Exception:
            return False


class BigQueryWarehouse(WarehouseStorage):
    """Google BigQuery implementation of WarehouseStorage.

    Delegates to BigQueryWriter and BigQueryLoader which
    operate through the shared BigQueryClient.
    """

    def __init__(
        self,
        project_id: str,
        dataset: str,
        credentials_path: str | None = None,
    ) -> None:
        self._client = BigQueryClient(project_id, dataset, credentials_path)
        self._writer = BigQueryWriter(self._client)
        self._loader = BigQueryLoader(self._client)

    async def write_gold(
        self,
        table: str,
        data: list[dict[str, Any]],
        schema: dict[str, type] | None = None,
    ) -> int:
        return await self._writer.write_gold(table, data, schema)

    async def execute_query(
        self,
        sql: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return await self._loader.execute_query(sql, params)

    async def create_table(self, table: str, schema: dict[str, type]) -> None:
        await self._loader.create_table(table, schema)

    async def truncate(self, table: str) -> None:
        await self._loader.truncate(table)

    async def table_exists(self, table: str) -> bool:
        return await self._loader.table_exists(table)
