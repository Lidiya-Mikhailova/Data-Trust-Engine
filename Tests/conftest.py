from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from Config import AppSettings


#Config

@pytest.fixture
def test_settings() -> AppSettings:
    return AppSettings(
        api_host="0.0.0.0",
        api_port=8000,
        logging__level="DEBUG",
    )


#Storage Mocks

@pytest.fixture
def mock_s3_client() -> MagicMock:
    client = MagicMock()
    client.write = AsyncMock()
    client.read = AsyncMock(return_value=b"{}")
    client.delete = AsyncMock()
    client.list = AsyncMock(return_value=[])
    client.exists = AsyncMock(return_value=True)
    return client


@pytest.fixture
def mock_bigquery_client() -> MagicMock:
    client = MagicMock()
    client.load = AsyncMock(return_value=100)
    client.query = AsyncMock(return_value=[])
    client.truncate = AsyncMock()
    client.table_exists = AsyncMock(return_value=True)
    return client


@pytest.fixture
def mock_sqlite_client() -> MagicMock:
    client = MagicMock()
    client.store = AsyncMock(return_value="rec_001")
    client.query = AsyncMock(return_value=[])
    client.delete = AsyncMock(return_value=True)
    return client


#Source Mocks

@pytest.fixture
def mock_primary_source_client() -> MagicMock:
    client = MagicMock()
    client.fetch = AsyncMock(return_value=[{"id": 1, "value": "a"}])
    client.health = AsyncMock(return_value=True)
    return client


@pytest.fixture
def mock_secondary_source_client() -> MagicMock:
    client = MagicMock()
    client.fetch = AsyncMock(return_value=[{"id": 1, "value": "b"}])
    client.health = AsyncMock(return_value=True)
    return client


#Sample Data

@pytest.fixture
def sample_raw_record() -> dict:
    return {"id": 1, "name": "test", "value": 42.0, "source": "primary"}


@pytest.fixture
def sample_raw_records() -> list[dict]:
    return [
        {"id": 1, "name": "alpha", "value": 10.0, "source": "primary"},
        {"id": 2, "name": "beta", "value": 20.0, "source": "primary"},
        {"id": 3, "name": "gamma", "value": 30.0, "source": "secondary"},
    ]


@pytest.fixture
def sample_standardized_records() -> list[dict]:
    return [
        {"record_id": 1, "entity": "alpha", "amount": 10.0, "origin": "primary"},
        {"record_id": 2, "entity": "beta", "amount": 20.0, "origin": "primary"},
        {"record_id": 3, "entity": "gamma", "amount": 30.0, "origin": "secondary"},
    ]
