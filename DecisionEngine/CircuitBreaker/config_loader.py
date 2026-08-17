from __future__ import annotations

import logging
from pathlib import Path

import yaml

from DecisionEngine.CircuitBreaker.models import CircuitBreakerConfig

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config" / "circuit_breaker.yml"


def load_config_from_yaml(
    source_id: str,
    config_path: str | Path | None = None,
) -> CircuitBreakerConfig:
    path = Path(config_path) if config_path else _DEFAULT_CONFIG_PATH

    with open(path) as f:
        data = yaml.safe_load(f)

    defaults = data.get("defaults", {})
    per_source = data.get("per_source", {}).get(source_id, {})
    merged = {**defaults, **per_source}

    return CircuitBreakerConfig(
        failure_threshold=merged.get("failure_threshold", CircuitBreakerConfig.failure_threshold),
        success_threshold=merged.get("success_threshold", CircuitBreakerConfig.success_threshold),
        recovery_timeout=merged.get("recovery_timeout", CircuitBreakerConfig.recovery_timeout),
        half_open_max_calls=merged.get("half_open_max_calls", CircuitBreakerConfig.half_open_max_calls),
    )


def load_all_configs(
    config_path: str | Path | None = None,
) -> dict[str, CircuitBreakerConfig]:
    path = Path(config_path) if config_path else _DEFAULT_CONFIG_PATH

    with open(path) as f:
        data = yaml.safe_load(f)

    defaults = data.get("defaults", {})
    per_source = data.get("per_source", {})

    configs: dict[str, CircuitBreakerConfig] = {}
    for source_id in per_source:
        merged = {**defaults, **per_source[source_id]}
        configs[source_id] = CircuitBreakerConfig(
            failure_threshold=merged.get("failure_threshold", CircuitBreakerConfig.failure_threshold),
            success_threshold=merged.get("success_threshold", CircuitBreakerConfig.success_threshold),
            recovery_timeout=merged.get("recovery_timeout", CircuitBreakerConfig.recovery_timeout),
            half_open_max_calls=merged.get("half_open_max_calls", CircuitBreakerConfig.half_open_max_calls),
        )

    if not configs:
        configs["default"] = CircuitBreakerConfig(
            failure_threshold=defaults.get("failure_threshold", CircuitBreakerConfig.failure_threshold),
            success_threshold=defaults.get("success_threshold", CircuitBreakerConfig.success_threshold),
            recovery_timeout=defaults.get("recovery_timeout", CircuitBreakerConfig.recovery_timeout),
            half_open_max_calls=defaults.get("half_open_max_calls", CircuitBreakerConfig.half_open_max_calls),
        )

    return configs
