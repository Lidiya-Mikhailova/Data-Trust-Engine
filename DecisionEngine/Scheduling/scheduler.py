from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any, Optional

from DecisionEngine.CircuitBreaker import CircuitBreaker
from DecisionEngine.HealthCheck import HealthCheckProbe

logger = logging.getLogger(__name__)

ProbeOperation = Callable[[str], Awaitable[dict[str, Any]]]


class ProbeScheduler:
    def __init__(
        self,
        circuit_breakers: dict[str, CircuitBreaker],
        prober: HealthCheckProbe,
        probe_interval: float = 30.0,
    ) -> None:
        self._cbs = circuit_breakers
        self._prober = prober
        self._probe_interval = probe_interval
        self._running = False
        self._task: Optional[asyncio.Task[None]] = None

    @property
    def is_running(self) -> bool:
        return self._running

    def start(
        self,
        probe_operation: ProbeOperation,
    ) -> None:
        if self._running:
            logger.warning("Probe scheduler already running")
            return

        self._running = True
        self._task = asyncio.create_task(
            self._run_loop(probe_operation),
            name="probe-scheduler",
        )
        logger.info(
            "Probe scheduler started",
            extra={"interval": self._probe_interval, "sources": list(self._cbs.keys())},
        )

    def stop(self) -> None:
        if not self._running:
            return

        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info("Probe scheduler stopped")

    async def probe_once(
        self,
        source_id: str,
        probe_operation: ProbeOperation,
    ) -> None:
        cb = self._cbs.get(source_id)
        if cb is None:
            logger.warning("No circuit breaker for source", extra={"source_id": source_id})
            return

        probe = await self._prober.probe(source_id, lambda: probe_operation(source_id))
        old_state = cb.state
        cb.update_from_probe(probe)

        if cb.state != old_state:
            logger.info(
                "CB state changed after probe",
                extra={
                    "source_id": source_id,
                    "old_state": old_state.value,
                    "new_state": cb.state.value,
                },
            )

    async def _run_loop(self, probe_operation: ProbeOperation) -> None:
        while self._running:
            try:
                for source_id in list(self._cbs.keys()):
                    if not self._running:
                        break
                    await self.probe_once(source_id, probe_operation)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(
                    "Probe scheduler cycle failed",
                    extra={"error": str(exc)},
                )

            try:
                await asyncio.sleep(self._probe_interval)
            except asyncio.CancelledError:
                break
