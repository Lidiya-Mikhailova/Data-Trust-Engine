from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


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
