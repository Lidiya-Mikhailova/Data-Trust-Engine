from __future__ import annotations

import asyncio
import logging
import time

logger = logging.getLogger(__name__)


class ProbeThrottle:
    def __init__(
        self,
        probe_interval: float = 5.0,
        probe_timeout: float = 10.0,
    ) -> None:
        if probe_interval <= 0:
            raise ValueError("probe_interval must be positive")
        if probe_timeout <= 0:
            raise ValueError("probe_timeout must be positive")

        self._probe_interval = probe_interval
        self._probe_timeout = probe_timeout
        self._last_probe_time: dict[str, float] = {}
        self._active_probes: dict[str, asyncio.Event] = {}

    @property
    def probe_interval(self) -> float:
        return self._probe_interval

    @property
    def probe_timeout(self) -> float:
        return self._probe_timeout

    def can_probe(self, source_id: str) -> bool:
        if source_id in self._active_probes:
            return False

        last_time = self._last_probe_time.get(source_id)
        if last_time is not None:
            elapsed = time.time() - last_time
            if elapsed < self._probe_interval:
                return False

        return True

    def acquire(self, source_id: str) -> bool:
        if not self.can_probe(source_id):
            logger.debug(
                "Probe throttled",
                extra={"source_id": source_id},
            )
            return False

        self._active_probes[source_id] = asyncio.Event()
        self._last_probe_time[source_id] = time.time()
        logger.debug(
            "Probe acquired",
            extra={"source_id": source_id},
        )
        return True

    def release(self, source_id: str) -> None:
        event = self._active_probes.pop(source_id, None)
        if event is not None:
            event.set()
        self._last_probe_time[source_id] = time.time()
        logger.debug(
            "Probe released",
            extra={"source_id": source_id},
        )

    def is_active(self, source_id: str) -> bool:
        return source_id in self._active_probes
