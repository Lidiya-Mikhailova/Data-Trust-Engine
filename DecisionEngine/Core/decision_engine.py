from __future__ import annotations

import logging
from typing import Any, Optional

from DecisionEngine.Alerts import AlertManager
from DecisionEngine.CircuitBreaker import CircuitBreaker, CircuitBreakerConfig, CircuitState
from DecisionEngine.CircuitBreaker.config_loader import load_config_from_yaml
from DecisionEngine.Core.models import DecisionAction, DecisionRequest, DecisionResult
from DecisionEngine.HealthCheck import HealthCheckProbe, HealthProbeResult
from DecisionEngine.Routing import FailoverRouter, SwitchRules
from DecisionEngine.StateStore import CBStateStore

logger = logging.getLogger(__name__)


class DecisionEngine:
    def __init__(
        self,
        source_ids: list[str],
        config_loader: Any = None,
        state_store: Optional[CBStateStore] = None,
        switch_rules: Optional[SwitchRules] = None,
        alert_manager: Optional[AlertManager] = None,
    ) -> None:
        self._source_ids = source_ids
        self._switch_rules = switch_rules or SwitchRules()
        self._alert_manager = alert_manager or AlertManager()
        self._state_store = state_store

        self._cbs: dict[str, CircuitBreaker] = {}
        for source_id in source_ids:
            config = self._load_config(source_id)
            cb = CircuitBreaker(source_id=source_id, config=config)
            self._restore_cb_state(cb, source_id)
            self._cbs[source_id] = cb

        self._router = FailoverRouter(
            circuit_breakers=self._cbs,
            allow_failover=self._switch_rules.trust_score_threshold > 0,
        )
        self._previous_states: dict[str, CircuitState] = {
            sid: CircuitState.CLOSED for sid in source_ids
        }

    def decide(self, request: DecisionRequest) -> DecisionResult:
        source_id = request.source_id
        cb = self._cbs.get(source_id)

        if cb is None:
            return DecisionResult(
                action=DecisionAction.SKIP,
                target_source=source_id,
                reason=f"Unknown source: {source_id}",
            )

        if request.health_probe is not None:
            cb.update_from_probe(request.health_probe)

        preferred = self._router.get_preferred_source(source_id)

        if preferred is None:
            self._alert_manager.on_source_unavailable(
                source_id=source_id,
                reason="Source unavailable and no fallback found",
            )
            return DecisionResult(
                action=DecisionAction.SKIP,
                target_source=source_id,
                reason="Source unavailable, no fallback",
            )

        if preferred != source_id:
            self._handle_failover(source_id, preferred)
            return DecisionResult(
                action=DecisionAction.FAILOVER,
                target_source=preferred,
                reason=f"Source {source_id} unavailable",
                fallback_source=preferred,
            )

        if self._switch_rules.should_failover(request.trust_score, request.latency_ms):
            fallback = self._router._find_fallback(source_id)
            if fallback:
                self._handle_failover(source_id, fallback)
                return DecisionResult(
                    action=DecisionAction.FAILOVER,
                    target_source=fallback,
                    reason="Trust score or latency threshold not met",
                    fallback_source=fallback,
                )
            return DecisionResult(
                action=DecisionAction.RETRY,
                target_source=source_id,
                reason="Thresholds not met, no fallback available",
            )

        return DecisionResult(
            action=DecisionAction.USE_SOURCE,
            target_source=source_id,
            reason="Source available and thresholds met",
        )

    def update_source(
        self,
        source_id: str,
        probe: HealthProbeResult,
    ) -> None:
        cb = self._cbs.get(source_id)
        if cb is None:
            return

        old_state = cb.state
        cb.update_from_probe(probe)
        self._check_and_notify(source_id, old_state, cb)

    def persist_all_states(self) -> None:
        if self._state_store is None:
            return
        for source_id, cb in self._cbs.items():
            state_dict = cb.save_state()
            self._state_store.put(source_id, state_dict)

    def get_cb_state(self, source_id: str) -> Optional[CircuitState]:
        cb = self._cbs.get(source_id)
        return cb.state if cb else None

    def get_cb_config(self, source_id: str) -> Optional[CircuitBreakerConfig]:
        cb = self._cbs.get(source_id)
        return cb.config if cb else None

    def reset_source(self, source_id: str) -> None:
        cb = self._cbs.get(source_id)
        if cb is None:
            return
        old_state = cb.state
        cb.reset()
        self._check_and_notify(source_id, old_state, cb)

    def get_available_sources(self) -> list[str]:
        return self._router.get_available_sources()

    def _handle_failover(self, from_source: str, to_source: str) -> None:
        self._alert_manager.on_failover(
            from_source=from_source,
            to_source=to_source,
            reason=f"Failover from {from_source} to {to_source}",
        )
        logger.warning(
            "Failover triggered",
            extra={"from_source": from_source, "to_source": to_source},
        )

    def _check_and_notify(
        self,
        source_id: str,
        old_state: CircuitState,
        cb: CircuitBreaker,
    ) -> None:
        if cb.state != old_state:
            self._alert_manager.on_state_transition(
                source_id=source_id,
                old_state=old_state.value,
                new_state=cb.state.value,
            )
            self._previous_states[source_id] = cb.state

    def _load_config(self, source_id: str) -> CircuitBreakerConfig:
        try:
            return load_config_from_yaml(source_id)
        except Exception as exc:
            logger.warning(
                "Failed to load CB config, using defaults",
                extra={"source_id": source_id, "error": str(exc)},
            )
            return CircuitBreakerConfig()

    def _restore_cb_state(self, cb: CircuitBreaker, source_id: str) -> None:
        if self._state_store is None:
            return
        state_dict = self._state_store.get(source_id)
        if state_dict is not None:
            cb.restore_state(state_dict)
            logger.info(
                "CB state restored from store",
                extra={"source_id": source_id, "state": cb.state.value},
            )
