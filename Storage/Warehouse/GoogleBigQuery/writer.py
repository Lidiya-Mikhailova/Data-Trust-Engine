from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from Storage.Warehouse.GoogleBigQuery.client import BigQueryClient


class BigQueryWriter:
    """Handles all write operations for BigQuery Warehouse."""

    def __init__(self, client: BigQueryClient) -> None:
        self._client = client

    async def write_gold(
        self,
        table: str,
        data: list[dict[str, Any]],
        schema: dict[str, type] | None = None,
    ) -> int:
        return await self._client.insert_rows(table, data)
