from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertManager:
    def __init__(self) -> None:
        self._handlers: list = []

    def register_handler(self, handler: Any) -> None:
        self._handlers.append(handler)

    def on_state_transition(
        self,
        source_id: str,
        old_state: str,
        new_state: str,
    ) -> None:
        severity = self._transition_severity(old_state, new_state)
        alert = {
            "type": "state_transition",
            "source_id": source_id,
            "old_state": old_state,
            "new_state": new_state,
            "severity": severity.value,
        }
        self._dispatch(alert)

    def on_failover(
        self,
        from_source: str,
        to_source: str,
        reason: str,
    ) -> None:
        alert = {
            "type": "failover",
            "from_source": from_source,
            "to_source": to_source,
            "reason": reason,
            "severity": AlertSeverity.WARNING.value,
        }
        self._dispatch(alert)

    def on_source_unavailable(
        self,
        source_id: str,
        reason: str,
    ) -> None:
        alert = {
            "type": "source_unavailable",
            "source_id": source_id,
            "reason": reason,
            "severity": AlertSeverity.CRITICAL.value,
        }
        self._dispatch(alert)

    def _dispatch(self, alert: dict[str, Any]) -> None:
        logger.warning(
            "Alert dispatched",
            extra={"alert_type": alert["type"], "severity": alert["severity"]},
        )
        for handler in self._handlers:
            try:
                handler(alert)
            except Exception as exc:
                logger.error(
                    "Alert handler failed",
                    extra={"error": str(exc)},
                )

    @staticmethod
    def _transition_severity(old_state: str, new_state: str) -> AlertSeverity:
        if new_state == "open":
            return AlertSeverity.CRITICAL
        if old_state == "open" and new_state == "half_open":
            return AlertSeverity.INFO
        if old_state == "half_open" and new_state == "closed":
            return AlertSeverity.INFO
        return AlertSeverity.WARNING
