from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from Storage.ObservabilityDB.SQLite.client import SQLiteClient


class SQLiteWriter:
    """Handles all insert operations for SQLite Observability DB."""

    def __init__(self, client: SQLiteClient) -> None:
        self._client = client

    async def write_metric(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        labels_json = json.dumps(labels) if labels else None
        await self._client.execute(
            "INSERT INTO metrics (name, value, labels, created_at) VALUES (?, ?, ?, ?)",
            (name, value, labels_json, now),
        )
        await self._client.commit()

    async def write_event(
        self,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        payload_json = json.dumps(payload)
        await self._client.execute(
            "INSERT INTO events (event_type, payload, created_at) VALUES (?, ?, ?)",
            (event_type, payload_json, now),
        )
        await self._client.commit()
