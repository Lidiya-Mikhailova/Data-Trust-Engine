from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ProbeStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNREACHABLE = "unreachable"


@dataclass(frozen=True)
class HealthProbeResult:
    source_id: str
    status: ProbeStatus
    latency_ms: float
    checked_at: float
    error_message: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
