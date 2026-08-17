from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class SourceHealthState:
    source_id: str
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    consecutive_success_in_half_open: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    last_state_change: float = field(default_factory=time.time)

    def record_success(self) -> None:
        self.success_count += 1
        self.last_success_time = time.time()
        if self.state == CircuitState.HALF_OPEN:
            self.consecutive_success_in_half_open += 1
        else:
            self.failure_count = 0

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.state == CircuitState.HALF_OPEN:
            self.consecutive_success_in_half_open = 0

    def reset(self) -> None:
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.consecutive_success_in_half_open = 0
        self.last_failure_time = None
        self.last_success_time = None
        self.last_state_change = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "consecutive_success_in_half_open": self.consecutive_success_in_half_open,
            "last_failure_time": self.last_failure_time,
            "last_success_time": self.last_success_time,
            "last_state_change": self.last_state_change,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SourceHealthState:
        return cls(
            source_id=data["source_id"],
            state=CircuitState(data["state"]),
            failure_count=data.get("failure_count", 0),
            success_count=data.get("success_count", 0),
            consecutive_success_in_half_open=data.get("consecutive_success_in_half_open", 0),
            last_failure_time=data.get("last_failure_time"),
            last_success_time=data.get("last_success_time"),
            last_state_change=data.get("last_state_change", time.time()),
        )
