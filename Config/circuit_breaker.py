from pydantic import BaseModel, Field

from Config.defaults import (
    ALLOW_SOURCE_FAILOVER_DEFAULT,
    CIRCUIT_BREAKER_FAILURE_THRESHOLD_DEFAULT,
    CIRCUIT_BREAKER_SUCCESS_THRESHOLD_DEFAULT,
    CIRCUIT_BREAKER_TIMEOUT_DEFAULT,
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
    timeout: int = Field(
        CIRCUIT_BREAKER_TIMEOUT_DEFAULT,
        validation_alias="CIRCUIT_BREAKER_TIMEOUT",
    )
    trust_score_threshold: float = Field(
        TRUST_SCORE_THRESHOLD_DEFAULT,
        validation_alias="TRUST_SCORE_THRESHOLD",
    )
    allow_source_failover: bool = Field(
        ALLOW_SOURCE_FAILOVER_DEFAULT,
        validation_alias="ALLOW_SOURCE_FAILOVER",
    )
