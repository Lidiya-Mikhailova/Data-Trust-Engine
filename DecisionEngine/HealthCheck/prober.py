from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Optional

from DecisionEngine.HealthCheck.models import HealthProbeResult, ProbeStatus
from DecisionEngine.HealthCheck.probe_throttle import ProbeThrottle

logger = logging.getLogger(__name__)

ProbeOperation = Callable[[], Awaitable[dict]]


class HealthCheckProbe:
    def __init__(
        self,
        throttle: Optional[ProbeThrottle] = None,
        probe_timeout: float = 10.0,
    ) -> None:
        self._throttle = throttle or ProbeThrottle()
        self._probe_timeout = probe_timeout

    async def probe(
        self,
        source_id: str,
        operation: ProbeOperation,
    ) -> HealthProbeResult:
        if not self._throttle.acquire(source_id):
            return HealthProbeResult(
                source_id=source_id,
                status=ProbeStatus.DEGRADED,
                latency_ms=-1.0,
                checked_at=time.time(),
                error_message="Probe throttled",
            )

        try:
            return await self._execute_probe(source_id, operation)
        finally:
            self._throttle.release(source_id)

    async def _execute_probe(
        self,
        source_id: str,
        operation: ProbeOperation,
    ) -> HealthProbeResult:
        start = time.monotonic()
        try:
            result = await asyncio.wait_for(
                operation(),
                timeout=self._throttle.probe_timeout,
            )
            latency_ms = (time.monotonic() - start) * 1000
            logger.info(
                "Health probe succeeded",
                extra={"source_id": source_id, "latency_ms": round(latency_ms, 2)},
            )
            return HealthProbeResult(
                source_id=source_id,
                status=ProbeStatus.HEALTHY,
                latency_ms=round(latency_ms, 2),
                checked_at=time.time(),
                metadata=result if isinstance(result, dict) else {},
            )
        except asyncio.TimeoutError:
            latency_ms = (time.monotonic() - start) * 1000
            logger.warning(
                "Health probe timed out",
                extra={"source_id": source_id, "latency_ms": round(latency_ms, 2)},
            )
            return HealthProbeResult(
                source_id=source_id,
                status=ProbeStatus.UNREACHABLE,
                latency_ms=round(latency_ms, 2),
                checked_at=time.time(),
                error_message="Probe timed out",
            )
        except Exception as exc:
            latency_ms = (time.monotonic() - start) * 1000
            logger.warning(
                "Health probe failed",
                extra={"source_id": source_id, "error": str(exc)},
            )
            return HealthProbeResult(
                source_id=source_id,
                status=ProbeStatus.UNREACHABLE,
                latency_ms=round(latency_ms, 2),
                checked_at=time.time(),
                error_message=str(exc),
            )
