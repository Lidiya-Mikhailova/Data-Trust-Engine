from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class DataLakeStorage(ABC):
    """Contract for raw data storage.

    Responsibility: persist raw ingestion payloads in object storage.
    Implementations must not contain business logic or data transformations.
    """

    @abstractmethod
    async def write_raw(self, key: str, data: bytes) -> None:
        """Persist raw bytes under the given key."""
        ...

    @abstractmethod
    async def read_raw(self, key: str) -> bytes:
        """Retrieve raw bytes by key."""
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check whether a key exists in the lake."""
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Remove an object by key."""
        ...

    @abstractmethod
    async def list_raw(self, prefix: str) -> list[str]:
        """Return all keys that share the given prefix."""
        ...


class WarehouseStorage(ABC):
    """Contract for analytical data warehouse.

    Responsibility: load processed (gold) data and execute analytical queries.
    Implementations must not contain business logic or data transformations.
    """

    @abstractmethod
    async def write_gold(
        self,
        table: str,
        data: list[dict[str, Any]],
        schema: Optional[dict[str, type]] = None,
    ) -> int:
        """Load gold-layer rows into *table*; return the number of rows written."""
        ...

    @abstractmethod
    async def execute_query(
        self,
        sql: str,
        params: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """Execute a read-only SQL statement and return the result set."""
        ...

    @abstractmethod
    async def create_table(self, table: str, schema: dict[str, type]) -> None:
        """Create a table with the given schema if it does not exist."""
        ...

    @abstractmethod
    async def truncate(self, table: str) -> None:
        """Remove all rows from *table*."""
        ...

    @abstractmethod
    async def table_exists(self, table: str) -> bool:
        """Return True if *table* exists in the warehouse."""
        ...


class ObservabilityStorage(ABC):
    """Contract for metrics and event persistence.

    Responsibility: store operational metrics, domain events, and health status.
    Implementations must not contain business logic or decision-making.
    """

    @abstractmethod
    async def write_metric(
        self,
        name: str,
        value: float,
        labels: Optional[dict[str, str]] = None,
    ) -> None:
        """Record a numeric metric with an optional label set."""
        ...

    @abstractmethod
    async def write_event(
        self,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        """Append a structured event to the observability store."""
        ...

    @abstractmethod
    async def get_health(self) -> dict[str, Any]:
        """Return a dictionary describing the current health of the store."""
        ...
