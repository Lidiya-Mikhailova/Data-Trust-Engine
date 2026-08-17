from __future__ import annotations

import logging
from typing import Optional

from DecisionEngine.CircuitBreaker import CircuitBreaker, CircuitState

logger = logging.getLogger(__name__)


class FailoverRouter:
    def __init__(
        self,
        circuit_breakers: dict[str, CircuitBreaker],
        allow_failover: bool = True,
    ) -> None:
        self._cbs = circuit_breakers
        self._allow_failover = allow_failover

    @property
    def allow_failover(self) -> bool:
        return self._allow_failover

    def get_available_sources(self) -> list[str]:
        return [source_id for source_id, cb in self._cbs.items() if cb.state != CircuitState.OPEN]

    def get_preferred_source(self, source_id: str) -> Optional[str]:
        cb = self._cbs.get(source_id)
        if cb is None:
            return source_id

        if cb.state != CircuitState.OPEN:
            return source_id

        if not self._allow_failover:
            return None

        return self._find_fallback(source_id)

    def _find_fallback(self, excluded_source: str) -> Optional[str]:
        for source_id, cb in self._cbs.items():
            if source_id == excluded_source:
                continue
            if cb.state == CircuitState.CLOSED:
                return source_id

        for source_id, cb in self._cbs.items():
            if source_id == excluded_source:
                continue
            if cb.state == CircuitState.HALF_OPEN:
                return source_id

        return None

    def is_source_available(self, source_id: str) -> bool:
        cb = self._cbs.get(source_id)
        if cb is None:
            return False
        return cb.state != CircuitState.OPEN
