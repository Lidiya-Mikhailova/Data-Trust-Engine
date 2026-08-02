from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional, Protocol, runtime_checkable


class Logger(ABC):
    """Contract for structured logging.

    Responsibility: emit structured log messages with severity levels.
    Implementations must not contain business logic or routing decisions.
    """

    @abstractmethod
    async def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        ...

    @abstractmethod
    async def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        ...

    @abstractmethod
    async def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        ...

    @abstractmethod
    async def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        ...

    @abstractmethod
    async def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        ...


@runtime_checkable
class LoggerProtocol(Protocol):
    """Structural contract for structured logging (Protocol variant)."""

    async def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        ...

    async def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        ...

    async def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        ...

    async def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        ...

    async def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        ...


class Metrics(ABC):
    """Contract for metrics collection.

    Responsibility: record application metrics (counters, gauges, histograms).
    Implementations must not contain business logic or alerting rules.
    """

    @abstractmethod
    async def counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[dict[str, str]] = None,
    ) -> None:
        ...

    @abstractmethod
    async def gauge(
        self,
        name: str,
        value: float,
        labels: Optional[dict[str, str]] = None,
    ) -> None:
        ...

    @abstractmethod
    async def histogram(
        self,
        name: str,
        value: float,
        labels: Optional[dict[str, str]] = None,
        buckets: Optional[list[float]] = None,
    ) -> None:
        ...


@runtime_checkable
class MetricsProtocol(Protocol):
    """Structural contract for metrics collection (Protocol variant)."""

    async def counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[dict[str, str]] = None,
    ) -> None:
        ...

    async def gauge(
        self,
        name: str,
        value: float,
        labels: Optional[dict[str, str]] = None,
    ) -> None:
        ...

    async def histogram(
        self,
        name: str,
        value: float,
        labels: Optional[dict[str, str]] = None,
        buckets: Optional[list[float]] = None,
    ) -> None:
        ...


class Tracing(ABC):
    """Contract for distributed tracing.

    Responsibility: manage trace spans for observability of request flows.
    Implementations must not contain business logic or routing decisions.
    """

    @abstractmethod
    async def start_span(
        self,
        name: str,
        attributes: Optional[dict[str, str]] = None,
    ) -> object:
        ...

    @abstractmethod
    async def end_span(self, span: object) -> None:
        ...


@runtime_checkable
class TracingProtocol(Protocol):
    """Structural contract for distributed tracing (Protocol variant)."""

    async def start_span(
        self,
        name: str,
        attributes: Optional[dict[str, str]] = None,
    ) -> object:
        ...

    async def end_span(self, span: object) -> None:
        ...


class HealthCheck(ABC):
    """Contract for service health probes.

    Responsibility: expose liveness / readiness state of a component.
    Implementations must not contain business logic or routing decisions.
    """

    @abstractmethod
    async def check(self) -> dict[str, Any]:
        ...

    @abstractmethod
    async def is_healthy(self) -> bool:
        ...


@runtime_checkable
class HealthCheckProtocol(Protocol):
    """Structural contract for service health probes (Protocol variant)."""

    async def check(self) -> dict[str, Any]:
        ...

    async def is_healthy(self) -> bool:
        ...
