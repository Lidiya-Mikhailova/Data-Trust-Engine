from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from typing import Generic, TypeVar, Union

from DecisionEngine.CircuitBreaker.source_state import CircuitState, SourceHealthState
from errors import CircuitBreakerError, CircuitBreakerTripped

logger = logging.getLogger(__name__)

T = TypeVar("T")

Operation = Union[Callable[[], T], Callable[[], Awaitable[T]]]


class CircuitBreaker(Generic[T]):
    def __init__(
        self,
        source_id: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        recovery_timeout: float = 30.0,
    ) -> None:
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        if success_threshold < 1:
            raise ValueError("success_threshold must be >= 1")
        if recovery_timeout <= 0:
            raise ValueError("recovery_timeout must be positive")

        self._state = SourceHealthState(source_id=source_id)
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.recovery_timeout = recovery_timeout

    #Public API

    @property
    def state(self) -> CircuitState:
        return self._state.state

    @property
    def source_id(self) -> str:
        return self._state.source_id

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
            raise CircuitBreakerError(
                f"Operation failed for source '{self._state.source_id}': {exc}"
            ) from exc

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
            raise CircuitBreakerError(
                f"Async operation failed for source '{self._state.source_id}': {exc}"
            ) from exc

    def reset(self) -> None:
        old_state = self._state.state
        self._state.reset()
        logger.info(
            "Circuit breaker reset",
            extra={"source_id": self._state.source_id, "old_state": old_state.value},
        )

    #Internal helpers

    def _check_open(self) -> None:
        if self._state.state == CircuitState.OPEN:
            if time.time() - self._state.last_state_change >= self.recovery_timeout:
                self._transition_to(CircuitState.HALF_OPEN)
            else:
                raise CircuitBreakerTripped(self._state.source_id)

    def _on_success(self) -> None:
        self._state.record_success()
        if self._state.state == CircuitState.HALF_OPEN:
            if self._state.consecutive_success_in_half_open >= self.success_threshold:
                self._transition_to(CircuitState.CLOSED)

    def _on_failure(self) -> None:
        self._state.record_failure()
        if self._state.state == CircuitState.CLOSED:
            if self._state.failure_count >= self.failure_threshold:
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
        elif new_state == CircuitState.OPEN:
            self._state.consecutive_success_in_half_open = 0

        logger.info(
            "Circuit breaker state transition",
            extra={
                "source_id": self._state.source_id,
                "old_state": old_state.value,
                "new_state": new_state.value,
            },
        )
