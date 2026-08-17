from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SwitchRules:
    trust_score_threshold: float = 0.80
    latency_threshold_ms: float = 500.0

    def should_use_source(
        self,
        trust_score: float,
        latency_ms: float,
    ) -> bool:
        return trust_score >= self.trust_score_threshold and latency_ms <= self.latency_threshold_ms

    def should_failover(
        self,
        trust_score: float,
        latency_ms: float,
    ) -> bool:
        return not self.should_use_source(trust_score, latency_ms)
