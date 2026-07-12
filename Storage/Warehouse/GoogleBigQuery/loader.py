from __future__ import annotations

from typing import TYPE_CHECKING, Any

from Storage.Warehouse.GoogleBigQuery.models import map_schema

if TYPE_CHECKING:
    from Storage.Warehouse.GoogleBigQuery.client import BigQueryClient


class BigQueryLoader:
    """Handles query execution, DDL and existence checks for BigQuery Warehouse."""

    def __init__(self, client: BigQueryClient) -> None:
        self._client = client

    async def execute_query(
        self,
        sql: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return await self._client.query(sql, params)

    async def create_table(self, table: str, schema: dict[str, type]) -> None:
        bq_schema = map_schema(schema)
        await self._client.create_table(table, bq_schema)

    async def truncate(self, table: str) -> None:
        await self._client.truncate_table(table)

    async def table_exists(self, table: str) -> bool:
        return await self._client.table_exists(table)
