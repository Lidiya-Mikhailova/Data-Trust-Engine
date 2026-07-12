from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Storage.ObservabilityDB.SQLite.client import SQLiteClient

_METRICS_DDL = """
CREATE TABLE IF NOT EXISTS metrics (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    value      REAL    NOT NULL,
    labels     TEXT,
    created_at TEXT    NOT NULL
);
"""

_EVENTS_DDL = """
CREATE TABLE IF NOT EXISTS events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT    NOT NULL,
    payload    TEXT    NOT NULL,
    created_at TEXT    NOT NULL
);
"""


class SQLiteMigration:
    """Manages schema creation for SQLite Observability DB."""

    def __init__(self, client: SQLiteClient) -> None:
        self._client = client
        self._ensured = False

    async def ensure_tables(self) -> None:
        if self._ensured:
            return
        await self._client.execute(_METRICS_DDL)
        await self._client.execute(_EVENTS_DDL)
        await self._client.commit()
        self._ensured = True
