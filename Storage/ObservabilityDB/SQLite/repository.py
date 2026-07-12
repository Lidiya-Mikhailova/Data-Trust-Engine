from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from Storage.ObservabilityDB.SQLite.client import SQLiteClient


class SQLiteRepository:
    """Handles read and health-check operations for SQLite Observability DB."""

    def __init__(self, client: SQLiteClient) -> None:
        self._client = client

    async def get_health(self) -> dict[str, Any]:
        return await self._client.health_check()
