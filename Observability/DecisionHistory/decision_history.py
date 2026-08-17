from __future__ import annotations

import logging

from Storage.interfaces import ObservabilityStorage

logger = logging.getLogger(__name__)

_EVENT_TYPE_CB_FAILOVER = "circuit_breaker_failover"
_EVENT_TYPE_CB_TRANSITION = "circuit_breaker_transition"


class DecisionHistory:
    def __init__(self, storage: ObservabilityStorage) -> None:
        self._storage = storage

    async def record_failover(
        self,
        from_source: str,
        to_source: str,
        reason: str,
    ) -> None:
        await self._storage.write_event(
            event_type=_EVENT_TYPE_CB_FAILOVER,
            payload={
                "from_source": from_source,
                "to_source": to_source,
                "reason": reason,
            },
        )
        logger.info(
            "Failover recorded",
            extra={"from_source": from_source, "to_source": to_source, "reason": reason},
        )

    async def record_transition(
        self,
        source_id: str,
        old_state: str,
        new_state: str,
    ) -> None:
        await self._storage.write_event(
            event_type=_EVENT_TYPE_CB_TRANSITION,
            payload={
                "source_id": source_id,
                "old_state": old_state,
                "new_state": new_state,
            },
        )
        logger.info(
            "State transition recorded",
            extra={"source_id": source_id, "old_state": old_state, "new_state": new_state},
        )
