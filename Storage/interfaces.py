from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional, Protocol, runtime_checkable


class DataLakeStorage(ABC):
    """Contract for raw data storage.

    Responsibility: persist raw ingestion payloads in object storage.
    Implementations must not contain business logic or data transformations.
    """

    @abstractmethod
    async def write_raw(self, key: str, data: bytes) -> None:
        ...

    @abstractmethod
    async def read_raw(self, key: str) -> bytes:
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        ...

    @abstractmethod
    async def list_raw(self, prefix: str) -> list[str]:
        ...

    @abstractmethod
    async def healthcheck(self) -> dict[str, Any]:
        ...


@runtime_checkable
class DataLakeStorageProtocol(Protocol):
    """Structural contract for raw data storage (Protocol variant)."""

    async def write_raw(self, key: str, data: bytes) -> None:
        ...

    async def read_raw(self, key: str) -> bytes:
        ...

    async def exists(self, key: str) -> bool:
        ...

    async def delete(self, key: str) -> None:
        ...

    async def list_raw(self, prefix: str) -> list[str]:
        ...

    async def healthcheck(self) -> dict[str, Any]:
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
        ...

    @abstractmethod
    async def execute_query(
        self,
        sql: str,
        params: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def create_table(self, table: str, schema: dict[str, type]) -> None:
        ...

    @abstractmethod
    async def truncate(self, table: str) -> None:
        ...

    @abstractmethod
    async def table_exists(self, table: str) -> bool:
        ...

    @abstractmethod
    async def healthcheck(self) -> dict[str, Any]:
        ...


@runtime_checkable
class WarehouseStorageProtocol(Protocol):
    """Structural contract for analytical data warehouse (Protocol variant)."""

    async def write_gold(
        self,
        table: str,
        data: list[dict[str, Any]],
        schema: Optional[dict[str, type]] = None,
    ) -> int:
        ...

    async def execute_query(
        self,
        sql: str,
        params: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        ...

    async def create_table(self, table: str, schema: dict[str, type]) -> None:
        ...

    async def truncate(self, table: str) -> None:
        ...

    async def table_exists(self, table: str) -> bool:
        ...

    async def healthcheck(self) -> dict[str, Any]:
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
        ...

    @abstractmethod
    async def write_event(
        self,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        ...

    @abstractmethod
    async def get_health(self) -> dict[str, Any]:
        ...


@runtime_checkable
class ObservabilityStorageProtocol(Protocol):
    """Structural contract for metrics and event persistence (Protocol variant)."""

    async def write_metric(
        self,
        name: str,
        value: float,
        labels: Optional[dict[str, str]] = None,
    ) -> None:
        ...

    async def write_event(
        self,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        ...

    async def get_health(self) -> dict[str, Any]:
        ...
