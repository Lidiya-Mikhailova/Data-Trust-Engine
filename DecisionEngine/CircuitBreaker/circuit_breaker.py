from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any, Generic, TypeVar, Union

from DecisionEngine.CircuitBreaker.models import CircuitBreakerConfig
from DecisionEngine.CircuitBreaker.source_state import CircuitState, SourceHealthState
from DecisionEngine.HealthCheck.models import HealthProbeResult, ProbeStatus
from errors import CircuitBreakerError, CircuitBreakerTripped

logger = logging.getLogger(__name__)

T = TypeVar("T")

Operation = Union[Callable[[], T], Callable[[], Awaitable[T]]]


class CircuitBreaker(Generic[T]):
    def __init__(
        self,
        source_id: str,
        config: CircuitBreakerConfig | None = None,
    ) -> None:
        self._config = config or CircuitBreakerConfig()
        self._state = SourceHealthState(source_id=source_id)
        self._half_open_calls: int = 0

    @property
    def config(self) -> CircuitBreakerConfig:
        return self._config

    @property
    def state(self) -> CircuitState:
        return self._state.state

    @property
    def source_id(self) -> str:
        return self._state.source_id

    @property
    def failure_threshold(self) -> int:
        return self._config.failure_threshold

    @property
    def success_threshold(self) -> int:
        return self._config.success_threshold

    @property
    def recovery_timeout(self) -> float:
        return self._config.recovery_timeout

    @property
    def health_state(self) -> SourceHealthState:
        return self._state

    def call(self, operation: Callable[[], T]) -> T:
        self._check_open()
        try:
            result = operation()
            self._on_success()
            return result
        except CircuitBreakerError:
            raise
        except Exception as exc:
            self._on_failure()
            raise CircuitBreakerError(f"Operation failed for source '{self._state.source_id}': {exc}") from exc

    async def async_call(self, operation: Callable[[], Awaitable[T]]) -> T:
        self._check_open()
        try:
            result = await operation()
            self._on_success()
            return result
        except CircuitBreakerError:
            raise
        except Exception as exc:
            self._on_failure()
            raise CircuitBreakerError(f"Async operation failed for source '{self._state.source_id}': {exc}") from exc

    def update_from_probe(self, probe: HealthProbeResult) -> None:
        if probe.status == ProbeStatus.HEALTHY:
            self._on_success()
        else:
            self._on_failure()

        logger.info(
            "Circuit breaker updated from health probe",
            extra={
                "source_id": self._state.source_id,
                "probe_status": probe.status.value,
                "new_state": self._state.state.value,
            },
        )

    def save_state(self) -> dict[str, Any]:
        return self._state.to_dict()

    def restore_state(self, data: dict[str, Any]) -> None:
        restored = SourceHealthState.from_dict(data)
        self._state = restored
        self._half_open_calls = 0  # in-flight probes are not persisted; reset on restore

        logger.info(
            "Circuit breaker state restored",
            extra={"source_id": self._state.source_id, "state": self._state.state.value},
        )

    def reset(self) -> None:
        old_state = self._state.state
        self._state.reset()
        self._half_open_calls = 0
        logger.info(
            "Circuit breaker reset",
            extra={"source_id": self._state.source_id, "old_state": old_state.value},
        )

    def _check_open(self) -> None:
        if self._state.state == CircuitState.OPEN:
            if time.time() - self._state.last_state_change >= self._config.recovery_timeout:
                self._transition_to(CircuitState.HALF_OPEN)
            else:
                raise CircuitBreakerTripped(self._state.source_id)

        if self._state.state == CircuitState.HALF_OPEN:
            if self._half_open_calls >= self._config.half_open_max_calls:
                raise CircuitBreakerTripped(self._state.source_id)
            self._half_open_calls += 1

    def _on_success(self) -> None:
        self._state.record_success()
        if self._state.state == CircuitState.HALF_OPEN:
            if self._state.consecutive_success_in_half_open >= self._config.success_threshold:
                self._transition_to(CircuitState.CLOSED)

    def _on_failure(self) -> None:
        self._state.record_failure()
        if self._state.state == CircuitState.CLOSED:
            if self._state.failure_count >= self._config.failure_threshold:
                self._transition_to(CircuitState.OPEN)
        elif self._state.state == CircuitState.HALF_OPEN:
            self._transition_to(CircuitState.OPEN)

    def _transition_to(self, new_state: CircuitState) -> None:
        old_state = self._state.state
        self._state.state = new_state
        self._state.last_state_change = time.time()

        if new_state == CircuitState.CLOSED:
            self._state.failure_count = 0
            self._state.consecutive_success_in_half_open = 0
            self._half_open_calls = 0
        elif new_state == CircuitState.OPEN:
            self._state.consecutive_success_in_half_open = 0
            self._half_open_calls = 0

        logger.info(
            "Circuit breaker state transition",
            extra={
                "source_id": self._state.source_id,
                "old_state": old_state.value,
                "new_state": new_state.value,
            },
        )
