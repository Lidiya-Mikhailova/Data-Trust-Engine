from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CircuitBreakerConfig:
    failure_threshold: int = 5
    success_threshold: int = 2
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 1

    def __post_init__(self) -> None:
        if self.failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        if self.success_threshold < 1:
            raise ValueError("success_threshold must be >= 1")
        if self.recovery_timeout <= 0:
            raise ValueError("recovery_timeout must be positive")
        if self.half_open_max_calls < 1:
            raise ValueError("half_open_max_calls must be >= 1")
