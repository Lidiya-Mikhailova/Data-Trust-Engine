from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class AbstractDataLake(ABC):
    @abstractmethod
    async def write(self, key: str, data: bytes) -> None: ...

    @abstractmethod
    async def read(self, key: str) -> bytes: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...

    @abstractmethod
    async def list(self, prefix: str) -> list[str]: ...

    @abstractmethod
    async def exists(self, key: str) -> bool: ...


class AbstractWarehouse(ABC):
    @abstractmethod
    async def load(
        self, table: str, data: list[dict[str, Any]], schema: Optional[dict[str, type]] = None
    ) -> int: ...

    @abstractmethod
    async def query(self, sql: str, params: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def truncate(self, table: str) -> None: ...

    @abstractmethod
    async def table_exists(self, table: str) -> bool: ...


class AbstractObservabilityDB(ABC):
    @abstractmethod
    async def store(self, collection: str, record: dict[str, Any]) -> str: ...

    @abstractmethod
    async def query(
        self, collection: str, filters: Optional[dict[str, Any]] = None
    ) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def delete(self, collection: str, record_id: str) -> bool: ...
