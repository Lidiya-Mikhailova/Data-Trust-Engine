from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from Storage.ObservabilityDB.SQLite.client import SQLiteClient, SQLiteObservabilityDB
from Storage.ObservabilityDB.SQLite.migration import SQLiteMigration
from Storage.ObservabilityDB.SQLite.repository import SQLiteRepository
from Storage.ObservabilityDB.SQLite.writer import SQLiteWriter


def _in_memory_client():
    real_connect = sqlite3.connect

    def patched_connect(db_path, **kwargs):
        return real_connect(db_path, check_same_thread=False, **kwargs)

    with patch("Storage.ObservabilityDB.SQLite.client.sqlite3.connect", side_effect=patched_connect):
        client = SQLiteClient(":memory:")
        client._get_connection()
    return client


class TestSQLiteClient:
    def test_db_path_property(self):
        client = SQLiteClient(":memory:")
        assert client.db_path == ":memory:"

    @pytest.mark.asyncio
    async def test_lazy_connection(self):
        client = _in_memory_client()
        assert client._connection is not None
        conn = client._get_connection()
        assert conn is client._get_connection()

    @pytest.mark.asyncio
    async def test_execute(self):
        client = _in_memory_client()
        await client.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, val TEXT)")
        cursor = await client.execute("INSERT INTO t (val) VALUES (?)", ("hello",))
        assert cursor.rowcount == 1
        await client.commit()

    @pytest.mark.asyncio
    async def test_executemany(self):
        client = _in_memory_client()
        await client.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, val TEXT)")
        await client.executemany(
            "INSERT INTO t (val) VALUES (?)",
            [("a",), ("b",), ("c",)],
        )
        await client.commit()
        rows = await client.fetchall("SELECT val FROM t ORDER BY id")
        assert [r["val"] for r in rows] == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_fetchall(self):
        client = _in_memory_client()
        await client.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, val TEXT)")
        await client.execute("INSERT INTO t (val) VALUES (?)", ("x",))
        await client.execute("INSERT INTO t (val) VALUES (?)", ("y",))
        await client.commit()
        rows = await client.fetchall("SELECT val FROM t ORDER BY id")
        assert len(rows) == 2
        assert rows[0]["val"] == "x"
        assert rows[1]["val"] == "y"

    @pytest.mark.asyncio
    async def test_fetchone(self):
        client = _in_memory_client()
        await client.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, val TEXT)")
        await client.execute("INSERT INTO t (val) VALUES (?)", ("only",))
        await client.commit()
        row = await client.fetchone("SELECT val FROM t WHERE id = 1")
        assert row is not None
        assert row["val"] == "only"

    @pytest.mark.asyncio
    async def test_fetchone_returns_none(self):
        client = _in_memory_client()
        await client.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
        await client.commit()
        row = await client.fetchone("SELECT * FROM t")
        assert row is None

    @pytest.mark.asyncio
    async def test_health_check_healthy(self):
        client = _in_memory_client()
        with patch(
            "Storage.ObservabilityDB.SQLite.client.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = datetime(2025, 1, 1, tzinfo=timezone.utc)
            result = await client.health_check()
        assert result["status"] == "healthy"
        assert result["timestamp"] == "2025-01-01T00:00:00+00:00"

    @pytest.mark.asyncio
    async def test_health_check_degraded(self):
        client = SQLiteClient(":memory:")
        client._connection = MagicMock()
        client._connection.execute.return_value.fetchone.return_value = None
        with patch(
            "Storage.ObservabilityDB.SQLite.client.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = datetime(2025, 1, 1, tzinfo=timezone.utc)
            result = await client.health_check()
        assert result["status"] == "degraded"


class TestSQLiteWriter:
    @pytest.mark.asyncio
    async def test_write_metric_with_labels(self):
        client = _in_memory_client()
        await client.execute(
            "CREATE TABLE metrics (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, "
            "value REAL NOT NULL, labels TEXT, created_at TEXT NOT NULL)"
        )
        await client.commit()
        writer = SQLiteWriter(client)
        with patch(
            "Storage.ObservabilityDB.SQLite.writer.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = datetime(2025, 6, 15, tzinfo=timezone.utc)
            await writer.write_metric("cpu_usage", 75.5, {"host": "web1"})
        rows = await client.fetchall("SELECT * FROM metrics")
        assert len(rows) == 1
        assert rows[0]["name"] == "cpu_usage"
        assert rows[0]["value"] == 75.5
        assert json.loads(rows[0]["labels"]) == {"host": "web1"}

    @pytest.mark.asyncio
    async def test_write_metric_without_labels(self):
        client = _in_memory_client()
        await client.execute(
            "CREATE TABLE metrics (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, "
            "value REAL NOT NULL, labels TEXT, created_at TEXT NOT NULL)"
        )
        await client.commit()
        writer = SQLiteWriter(client)
        with patch(
            "Storage.ObservabilityDB.SQLite.writer.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = datetime(2025, 6, 15, tzinfo=timezone.utc)
            await writer.write_metric("disk_io", 1024.0)
        rows = await client.fetchall("SELECT * FROM metrics")
        assert len(rows) == 1
        assert rows[0]["labels"] is None

    @pytest.mark.asyncio
    async def test_write_event(self):
        client = _in_memory_client()
        await client.execute(
            "CREATE TABLE events (id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "event_type TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL)"
        )
        await client.commit()
        writer = SQLiteWriter(client)
        with patch(
            "Storage.ObservabilityDB.SQLite.writer.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = datetime(2025, 6, 15, tzinfo=timezone.utc)
            await writer.write_event("pipeline_start", {"dag_id": "etl_001"})
        rows = await client.fetchall("SELECT * FROM events")
        assert len(rows) == 1
        assert rows[0]["event_type"] == "pipeline_start"
        assert json.loads(rows[0]["payload"]) == {"dag_id": "etl_001"}


class TestSQLiteMigration:
    @pytest.mark.asyncio
    async def test_ensure_tables_creates_tables(self):
        client = _in_memory_client()
        migration = SQLiteMigration(client)
        await migration.ensure_tables()
        await client.commit()
        tables = await client.fetchall(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        table_names = [t["name"] for t in tables]
        assert "metrics" in table_names
        assert "events" in table_names

    @pytest.mark.asyncio
    async def test_ensure_tables_idempotent(self):
        client = _in_memory_client()
        migration = SQLiteMigration(client)
        await migration.ensure_tables()
        await client.commit()
        await migration.ensure_tables()
        tables = await client.fetchall(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        table_names = [t["name"] for t in tables]
        assert table_names.count("metrics") == 1
        assert table_names.count("events") == 1


class TestSQLiteRepository:
    @pytest.mark.asyncio
    async def test_get_health(self):
        client = SQLiteClient(":memory:")
        repo = SQLiteRepository(client)
        with patch.object(client, "health_check", new_callable=AsyncMock) as mock_hc:
            mock_hc.return_value = {"status": "healthy", "timestamp": "2025-01-01T00:00:00+00:00"}
            result = await repo.get_health()
        assert result["status"] == "healthy"
        mock_hc.assert_awaited_once()


class TestSQLiteObservabilityDB:
    @pytest.mark.asyncio
    async def test_write_metric_creates_tables_and_writes(self):
        db = SQLiteObservabilityDB.__new__(SQLiteObservabilityDB)
        db._client = _in_memory_client()
        db._writer = SQLiteWriter(db._client)
        db._migration = SQLiteMigration(db._client)
        db._repository = SQLiteRepository(db._client)
        with patch(
            "Storage.ObservabilityDB.SQLite.writer.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = datetime(2025, 6, 15, tzinfo=timezone.utc)
            await db.write_metric("requests", 42.0, {"env": "prod"})
        rows = await db._client.fetchall("SELECT * FROM metrics")
        assert len(rows) == 1
        assert rows[0]["name"] == "requests"

    @pytest.mark.asyncio
    async def test_write_event_creates_tables_and_writes(self):
        db = SQLiteObservabilityDB.__new__(SQLiteObservabilityDB)
        db._client = _in_memory_client()
        db._writer = SQLiteWriter(db._client)
        db._migration = SQLiteMigration(db._client)
        db._repository = SQLiteRepository(db._client)
        with patch(
            "Storage.ObservabilityDB.SQLite.writer.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = datetime(2025, 6, 15, tzinfo=timezone.utc)
            await db.write_event("alert", {"level": "critical"})
        rows = await db._client.fetchall("SELECT * FROM events")
        assert len(rows) == 1
        assert rows[0]["event_type"] == "alert"

    @pytest.mark.asyncio
    async def test_get_health(self):
        db = SQLiteObservabilityDB.__new__(SQLiteObservabilityDB)
        db._client = _in_memory_client()
        db._writer = SQLiteWriter(db._client)
        db._migration = SQLiteMigration(db._client)
        db._repository = SQLiteRepository(db._client)
        result = await db.get_health()
        assert result["status"] == "healthy"
