from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from DecisionEngine.HealthCheck.models import HealthProbeResult


@dataclass(frozen=True)
class DecisionRequest:
    source_id: str
    trust_score: float
    latency_ms: float
    health_probe: Optional[HealthProbeResult] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class DecisionAction(Enum):
    USE_SOURCE = "use_source"
    FAILOVER = "failover"
    SKIP = "skip"
    RETRY = "retry"


@dataclass(frozen=True)
class DecisionResult:
    action: DecisionAction
    target_source: str
    reason: str
    fallback_source: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
