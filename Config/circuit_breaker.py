from pydantic import BaseModel, Field

from Config.defaults import (
    ALLOW_SOURCE_FAILOVER_DEFAULT,
    CIRCUIT_BREAKER_FAILURE_THRESHOLD_DEFAULT,
    CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS_DEFAULT,
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT_DEFAULT,
    CIRCUIT_BREAKER_SUCCESS_THRESHOLD_DEFAULT,
    TRUST_SCORE_THRESHOLD_DEFAULT,
)


class CircuitBreakerSettings(BaseModel):
    failure_threshold: int = Field(
        CIRCUIT_BREAKER_FAILURE_THRESHOLD_DEFAULT,
        validation_alias="CIRCUIT_BREAKER_FAILURE_THRESHOLD",
    )
    success_threshold: int = Field(
        CIRCUIT_BREAKER_SUCCESS_THRESHOLD_DEFAULT,
        validation_alias="CIRCUIT_BREAKER_SUCCESS_THRESHOLD",
    )
    recovery_timeout: int = Field(
        CIRCUIT_BREAKER_RECOVERY_TIMEOUT_DEFAULT,
        validation_alias="CIRCUIT_BREAKER_RECOVERY_TIMEOUT",
    )
    half_open_max_calls: int = Field(
        CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS_DEFAULT,
        validation_alias="CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS",
    )
    trust_score_threshold: float = Field(
        TRUST_SCORE_THRESHOLD_DEFAULT,
        validation_alias="TRUST_SCORE_THRESHOLD",
    )
    allow_source_failover: bool = Field(
        ALLOW_SOURCE_FAILOVER_DEFAULT,
        validation_alias="ALLOW_SOURCE_FAILOVER",
    )
