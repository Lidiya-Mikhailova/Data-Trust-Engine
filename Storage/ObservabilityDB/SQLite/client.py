from __future__ import annotations

import asyncio
import sqlite3
from datetime import datetime, timezone
from typing import Any

from Storage.ObservabilityDB.SQLite.migration import SQLiteMigration
from Storage.ObservabilityDB.SQLite.repository import SQLiteRepository
from Storage.ObservabilityDB.SQLite.writer import SQLiteWriter
from Storage.interfaces import ObservabilityStorage


class SQLiteClient:
    """Synchronous sqlite3 wrapper with asyncio.to_thread dispatch.

    All raw DB calls are routed through this class so that writer,
    migration and repository modules never import sqlite3 directly.
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._connection: sqlite3.Connection | None = None

    @property
    def db_path(self) -> str:
        return self._db_path

    def _get_connection(self) -> sqlite3.Connection:
        if self._connection is None:
            self._connection = sqlite3.connect(self._db_path)
            self._connection.row_factory = sqlite3.Row
        return self._connection

    async def execute(self, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Cursor:
        conn = self._get_connection()
        return await asyncio.to_thread(conn.execute, sql, params)

    async def executemany(self, sql: str, params: list[tuple[Any, ...]]) -> None:
        conn = self._get_connection()
        await asyncio.to_thread(conn.executemany, sql, params)

    async def fetchall(self, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        conn = self._get_connection()
        return await asyncio.to_thread(
            lambda: conn.execute(sql, params).fetchall(),
        )

    async def fetchone(self, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
        conn = self._get_connection()
        return await asyncio.to_thread(
            lambda: conn.execute(sql, params).fetchone(),
        )

    async def commit(self) -> None:
        conn = self._get_connection()
        await asyncio.to_thread(conn.commit)

    async def health_check(self) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        result = await self.fetchone("SELECT 1 AS ok")
        return {"status": "healthy" if result else "degraded", "timestamp": now}


class SQLiteObservabilityDB(ObservabilityStorage):
    """SQLite implementation of ObservabilityStorage.

    Delegates to SQLiteWriter, SQLiteMigration and SQLiteRepository
    which operate through the shared SQLiteClient.
    """

    def __init__(self, db_path: str) -> None:
        self._client = SQLiteClient(db_path)
        self._writer = SQLiteWriter(self._client)
        self._migration = SQLiteMigration(self._client)
        self._repository = SQLiteRepository(self._client)

    async def write_metric(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        await self._migration.ensure_tables()
        await self._writer.write_metric(name, value, labels)

    async def write_event(
        self,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        await self._migration.ensure_tables()
        await self._writer.write_event(event_type, payload)

    async def get_health(self) -> dict[str, Any]:
        return await self._repository.get_health()
