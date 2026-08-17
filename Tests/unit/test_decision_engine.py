from __future__ import annotations

import time
from unittest.mock import AsyncMock

import pytest

from DecisionEngine.Alerts import AlertManager
from DecisionEngine.CircuitBreaker import CircuitBreaker, CircuitBreakerConfig, CircuitState
from DecisionEngine.CircuitBreaker.config_loader import load_all_configs, load_config_from_yaml
from DecisionEngine.Core.decision_engine import DecisionEngine
from DecisionEngine.Core.models import DecisionAction, DecisionRequest, DecisionResult
from DecisionEngine.HealthCheck.models import HealthProbeResult, ProbeStatus
from DecisionEngine.Routing import FailoverRouter, SwitchRules
from DecisionEngine.StateStore import CBStateStore
from errors import CircuitBreakerError, CircuitBreakerTripped


class TestCircuitBreakerConfig:
    def test_default_config(self):
        config = CircuitBreakerConfig()
        assert config.failure_threshold == 5
        assert config.success_threshold == 2
        assert config.recovery_timeout == 30.0
        assert config.half_open_max_calls == 1

    def test_custom_config(self):
        config = CircuitBreakerConfig(
            failure_threshold=3, success_threshold=3, recovery_timeout=60.0, half_open_max_calls=2
        )
        assert config.failure_threshold == 3
        assert config.success_threshold == 3
        assert config.recovery_timeout == 60.0
        assert config.half_open_max_calls == 2

    def test_invalid_failure_threshold(self):
        with pytest.raises(ValueError, match="failure_threshold"):
            CircuitBreakerConfig(failure_threshold=0)

    def test_invalid_success_threshold(self):
        with pytest.raises(ValueError, match="success_threshold"):
            CircuitBreakerConfig(success_threshold=0)

    def test_invalid_timeout(self):
        with pytest.raises(ValueError, match="recovery_timeout"):
            CircuitBreakerConfig(recovery_timeout=0)

    def test_invalid_half_open_max_calls(self):
        with pytest.raises(ValueError, match="half_open_max_calls"):
            CircuitBreakerConfig(half_open_max_calls=0)


class TestCircuitBreakerCreation:
    def test_default_parameters(self):
        cb = CircuitBreaker("source-a")
        assert cb.source_id == "source-a"
        assert cb.failure_threshold == 5
        assert cb.success_threshold == 2
        assert cb.recovery_timeout == 30.0
        assert cb.state == CircuitState.CLOSED

    def test_custom_config(self):
        config = CircuitBreakerConfig(failure_threshold=3, success_threshold=3, recovery_timeout=60.0)
        cb = CircuitBreaker("source-b", config=config)
        assert cb.failure_threshold == 3
        assert cb.success_threshold == 3
        assert cb.recovery_timeout == 60.0

    def test_config_property(self):
        config = CircuitBreakerConfig(failure_threshold=7)
        cb = CircuitBreaker("source-c", config=config)
        assert cb.config is config
        assert cb.config.failure_threshold == 7


class TestCircuitBreakerClosedState:
    def test_successful_call_stays_closed(self):
        cb = CircuitBreaker("source-a", CircuitBreakerConfig(failure_threshold=3))
        result = cb.call(lambda: "ok")
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED

    def test_failure_increments_counter(self):
        cb = CircuitBreaker("source-a", CircuitBreakerConfig(failure_threshold=3))

        def fail():
            raise ValueError("boom")

        with pytest.raises(CircuitBreakerError):
            cb.call(fail)
        assert cb.state == CircuitState.CLOSED

    def test_failure_threshold_reached_trips_to_open(self):
        cb = CircuitBreaker("source-a", CircuitBreakerConfig(failure_threshold=3))

        def fail():
            raise ValueError("boom")

        for _ in range(2):
            with pytest.raises(CircuitBreakerError):
                cb.call(fail)

        assert cb.state == CircuitState.CLOSED

        with pytest.raises(CircuitBreakerError):
            cb.call(fail)

        assert cb.state == CircuitState.OPEN

    def test_success_resets_failure_counter(self):
        cb = CircuitBreaker("source-a", CircuitBreakerConfig(failure_threshold=3))

        def fail():
            raise ValueError("boom")

        def ok():
            return "ok"

        with pytest.raises(CircuitBreakerError):
            cb.call(fail)
        with pytest.raises(CircuitBreakerError):
            cb.call(fail)

        cb.call(ok)

        with pytest.raises(CircuitBreakerError):
            cb.call(fail)
        with pytest.raises(CircuitBreakerError):
            cb.call(fail)
        with pytest.raises(CircuitBreakerError):
            cb.call(fail)

        assert cb.state == CircuitState.OPEN


class TestCircuitBreakerOpenState:
    def test_immediate_rejection(self):
        cb = CircuitBreaker("source-a", CircuitBreakerConfig(failure_threshold=1, recovery_timeout=999))

        def fail():
            raise ValueError("boom")

        with pytest.raises(CircuitBreakerError):
            cb.call(fail)
        assert cb.state == CircuitState.OPEN

        def ok():
            return "ok"

        with pytest.raises(CircuitBreakerTripped, match="source-a"):
            cb.call(ok)

    def test_transition_to_half_open_after_timeout(self):
        cb = CircuitBreaker("source-a", CircuitBreakerConfig(failure_threshold=1, recovery_timeout=0.05))

        def fail():
            raise ValueError("boom")

        with pytest.raises(CircuitBreakerError):
            cb.call(fail)
        assert cb.state == CircuitState.OPEN

        time.sleep(0.06)

        def ok():
            return "ok"

        result = cb.call(ok)
        assert result == "ok"
        assert cb.state == CircuitState.HALF_OPEN

    def test_reset_closes_circuit(self):
        cb = CircuitBreaker("source-a", CircuitBreakerConfig(failure_threshold=1))

        def fail():
            raise ValueError("boom")

        with pytest.raises(CircuitBreakerError):
            cb.call(fail)
        assert cb.state == CircuitState.OPEN

        cb.reset()
        assert cb.state == CircuitState.CLOSED


class TestCircuitBreakerHalfOpenState:
    def test_success_threshold_closes_circuit(self):
        config = CircuitBreakerConfig(failure_threshold=1, success_threshold=2, recovery_timeout=0.05, half_open_max_calls=2)
        cb = CircuitBreaker("source-a", config)

        def fail():
            raise ValueError("boom")

        with pytest.raises(CircuitBreakerError):
            cb.call(fail)
        assert cb.state == CircuitState.OPEN

        time.sleep(0.06)

        def ok():
            return "ok"

        cb.call(ok)
        assert cb.state == CircuitState.HALF_OPEN

        cb.call(ok)
        assert cb.state == CircuitState.CLOSED

    def test_failure_in_half_open_goes_back_to_open(self):
        config = CircuitBreakerConfig(failure_threshold=1, success_threshold=2, recovery_timeout=0.05)
        cb = CircuitBreaker("source-a", config)

        def fail():
            raise ValueError("boom")

        with pytest.raises(CircuitBreakerError):
            cb.call(fail)
        assert cb.state == CircuitState.OPEN

        time.sleep(0.06)

        def fail_again():
            raise ValueError("still broken")

        with pytest.raises(CircuitBreakerError):
            cb.call(fail_again)
        assert cb.state == CircuitState.OPEN

    def test_half_open_max_calls_blocks_excess(self):
        config = CircuitBreakerConfig(failure_threshold=1, success_threshold=3, recovery_timeout=0.05, half_open_max_calls=1)
        cb = CircuitBreaker("source-a", config)

        def fail():
            raise ValueError("boom")

        with pytest.raises(CircuitBreakerError):
            cb.call(fail)
        assert cb.state == CircuitState.OPEN

        time.sleep(0.06)

        def ok():
            return "ok"

        cb.call(ok)
        assert cb.state == CircuitState.HALF_OPEN

        with pytest.raises(CircuitBreakerTripped, match="source-a"):
            cb.call(ok)

    def test_half_open_calls_reset_on_transition_to_closed(self):
        config = CircuitBreakerConfig(failure_threshold=1, success_threshold=2, recovery_timeout=0.05, half_open_max_calls=5)
        cb = CircuitBreaker("source-a", config)

        def fail():
            raise ValueError("boom")

        with pytest.raises(CircuitBreakerError):
            cb.call(fail)

        time.sleep(0.06)

        def ok():
            return "ok"

        cb.call(ok)
        cb.call(ok)
        assert cb.state == CircuitState.CLOSED

        time.sleep(0.06)

        cb.call(ok)
        assert cb.state == CircuitState.CLOSED


class TestCircuitBreakerErrorPassthrough:
    def test_sync_call_reraises_circuit_breaker_error(self):
        cb = CircuitBreaker("source-a")

        def raise_cb_error():
            raise CircuitBreakerError("original error")

        with pytest.raises(CircuitBreakerError, match="original error"):
            cb.call(raise_cb_error)

    @pytest.mark.asyncio
    async def test_async_call_reraises_circuit_breaker_error(self):
        cb = CircuitBreaker("source-a")

        async def raise_cb_error():
            raise CircuitBreakerError("original error")

        with pytest.raises(CircuitBreakerError, match="original error"):
            await cb.async_call(raise_cb_error)


class TestAsyncCircuitBreaker:
    @pytest.mark.asyncio
    async def test_successful_async_call(self):
        cb = CircuitBreaker("source-a", CircuitBreakerConfig(failure_threshold=3))

        async def ok():
            return "ok"

        result = await cb.async_call(ok)
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_failure_trips_circuit(self):
        cb = CircuitBreaker("source-a", CircuitBreakerConfig(failure_threshold=1))

        async def fail():
            raise RuntimeError("boom")

        with pytest.raises(CircuitBreakerError):
            await cb.async_call(fail)
        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_tripped_rejects_async_call(self):
        cb = CircuitBreaker("source-a", CircuitBreakerConfig(failure_threshold=1, recovery_timeout=999))

        async def fail():
            raise RuntimeError("boom")

        with pytest.raises(CircuitBreakerError):
            await cb.async_call(fail)

        async def ok():
            return "ok"

        with pytest.raises(CircuitBreakerTripped):
            await cb.async_call(ok)

    @pytest.mark.asyncio
    async def test_async_half_open_max_calls(self):
        config = CircuitBreakerConfig(failure_threshold=1, success_threshold=3, recovery_timeout=0.05, half_open_max_calls=1)
        cb = CircuitBreaker("source-a", config)

        async def fail():
            raise RuntimeError("boom")

        with pytest.raises(CircuitBreakerError):
            await cb.async_call(fail)

        time.sleep(0.06)

        async def ok():
            return "ok"

        await cb.async_call(ok)
        assert cb.state == CircuitState.HALF_OPEN

        with pytest.raises(CircuitBreakerTripped):
            await cb.async_call(ok)


class TestUpdateFromProbe:
    def test_healthy_probe_stays_closed(self):
        cb = CircuitBreaker("source-a")
        probe = HealthProbeResult(source_id="source-a", status=ProbeStatus.HEALTHY, latency_ms=50.0, checked_at=time.time())
        cb.update_from_probe(probe)
        assert cb.state == CircuitState.CLOSED

    def test_unhealthy_probe_increments_failure(self):
        cb = CircuitBreaker("source-a", CircuitBreakerConfig(failure_threshold=3))
        probe = HealthProbeResult(source_id="source-a", status=ProbeStatus.UNREACHABLE, latency_ms=5000.0, checked_at=time.time(), error_message="timeout")
        cb.update_from_probe(probe)
        assert cb.state == CircuitState.CLOSED
        assert cb.health_state.failure_count == 1

    def test_unhealthy_probe_trips_to_open(self):
        cb = CircuitBreaker("source-a", CircuitBreakerConfig(failure_threshold=2))
        probe = HealthProbeResult(source_id="source-a", status=ProbeStatus.UNREACHABLE, latency_ms=5000.0, checked_at=time.time())
        cb.update_from_probe(probe)
        assert cb.state == CircuitState.CLOSED
        cb.update_from_probe(probe)
        assert cb.state == CircuitState.OPEN

    def test_healthy_probe_resets_failure_counter(self):
        cb = CircuitBreaker("source-a", CircuitBreakerConfig(failure_threshold=3))
        probe_fail = HealthProbeResult(source_id="source-a", status=ProbeStatus.UNREACHABLE, latency_ms=5000.0, checked_at=time.time())
        probe_ok = HealthProbeResult(source_id="source-a", status=ProbeStatus.HEALTHY, latency_ms=50.0, checked_at=time.time())
        cb.update_from_probe(probe_fail)
        cb.update_from_probe(probe_ok)
        assert cb.health_state.failure_count == 0


class TestStatePersistence:
    def test_save_state_returns_dict(self):
        cb = CircuitBreaker("source-a")
        state_dict = cb.save_state()
        assert state_dict["source_id"] == "source-a"
        assert state_dict["state"] == "closed"
        assert "failure_count" in state_dict
        assert "last_state_change" in state_dict

    def test_restore_state(self):
        cb = CircuitBreaker("source-a")
        state_dict = {
            "source_id": "source-a",
            "state": "open",
            "failure_count": 5,
            "success_count": 10,
            "consecutive_success_in_half_open": 0,
            "last_failure_time": time.time() - 10,
            "last_success_time": time.time() - 5,
            "last_state_change": time.time() - 10,
        }
        cb.restore_state(state_dict)
        assert cb.state == CircuitState.OPEN
        assert cb.health_state.failure_count == 5

    def test_save_restore_roundtrip(self):
        cb = CircuitBreaker("source-a", CircuitBreakerConfig(failure_threshold=3))

        def fail():
            raise ValueError("boom")

        for _ in range(2):
            with pytest.raises(CircuitBreakerError):
                cb.call(fail)

        state_dict = cb.save_state()

        cb2 = CircuitBreaker("source-a")
        cb2.restore_state(state_dict)
        assert cb2.state == cb.state
        assert cb2.health_state.failure_count == cb.health_state.failure_count


class TestConfigLoader:
    def test_load_default_config(self):
        config = load_config_from_yaml("primary")
        assert config.failure_threshold == 5
        assert config.success_threshold == 2
        assert config.recovery_timeout == 30

    def test_load_secondary_config(self):
        config = load_config_from_yaml("secondary")
        assert config.failure_threshold == 3
        assert config.success_threshold == 3
        assert config.recovery_timeout == 15

    def test_load_unknown_source_uses_defaults(self):
        config = load_config_from_yaml("unknown_source")
        assert config.failure_threshold == 5
        assert config.success_threshold == 2
        assert config.recovery_timeout == 30

    def test_load_all_configs(self):
        configs = load_all_configs()
        assert "primary" in configs
        assert "secondary" in configs
        assert configs["primary"].failure_threshold == 5
        assert configs["secondary"].failure_threshold == 3


class TestCBStateStore:
    def test_put_and_get(self):
        store = CBStateStore()
        store.put("primary", {"state": "open", "failure_count": 5})
        result = store.get("primary")
        assert result is not None
        assert result["state"] == "open"
        assert result["failure_count"] == 5

    def test_get_nonexistent_returns_none(self):
        store = CBStateStore()
        assert store.get("nonexistent") is None

    def test_delete(self):
        store = CBStateStore()
        store.put("primary", {"state": "open"})
        store.delete("primary")
        assert store.get("primary") is None

    def test_delete_nonexistent_no_error(self):
        store = CBStateStore()
        store.delete("nonexistent")

    def test_list_sources(self):
        store = CBStateStore()
        store.put("primary", {"state": "open"})
        store.put("secondary", {"state": "closed"})
        sources = store.list_sources()
        assert sorted(sources) == ["primary", "secondary"]

    def test_clear(self):
        store = CBStateStore()
        store.put("primary", {"state": "open"})
        store.put("secondary", {"state": "closed"})
        store.clear()
        assert store.list_sources() == []

    def test_persistence_to_file(self, tmp_path):
        path = str(tmp_path / "cb_state.json")
        store = CBStateStore(persist_path=path)
        store.put("primary", {"state": "open", "failure_count": 5})

        store2 = CBStateStore(persist_path=path)
        result = store2.get("primary")
        assert result is not None
        assert result["state"] == "open"
        assert result["failure_count"] == 5

    def test_load_from_nonexistent_file(self, tmp_path):
        path = str(tmp_path / "nonexistent.json")
        store = CBStateStore(persist_path=path)
        assert store.list_sources() == []

    def test_overwrite_existing_state(self):
        store = CBStateStore()
        store.put("primary", {"state": "closed"})
        store.put("primary", {"state": "open"})
        result = store.get("primary")
        assert result["state"] == "open"

    def test_multiple_sources_independent(self):
        store = CBStateStore()
        store.put("primary", {"state": "closed", "failure_count": 0})
        store.put("secondary", {"state": "open", "failure_count": 5})
        assert store.get("primary")["state"] == "closed"
        assert store.get("secondary")["state"] == "open"
        store.delete("primary")
        assert store.get("primary") is None
        assert store.get("secondary")["state"] == "open"


class TestFailoverRouter:
    def test_preferred_source_when_closed(self):
        cb = CircuitBreaker("primary")
        router = FailoverRouter({"primary": cb}, allow_failover=True)
        assert router.get_preferred_source("primary") == "primary"

    def test_preferred_source_when_open_fallback(self):
        cb_primary = CircuitBreaker("primary")
        cb_secondary = CircuitBreaker("secondary")
        cb_primary._state.state = CircuitState.OPEN
        router = FailoverRouter({"primary": cb_primary, "secondary": cb_secondary}, allow_failover=True)
        assert router.get_preferred_source("primary") == "secondary"

    def test_preferred_source_when_open_no_fallback(self):
        cb_primary = CircuitBreaker("primary")
        cb_primary._state.state = CircuitState.OPEN
        router = FailoverRouter({"primary": cb_primary}, allow_failover=False)
        assert router.get_preferred_source("primary") is None

    def test_available_sources_excludes_open(self):
        cb_primary = CircuitBreaker("primary")
        cb_secondary = CircuitBreaker("secondary")
        cb_primary._state.state = CircuitState.OPEN
        router = FailoverRouter({"primary": cb_primary, "secondary": cb_secondary})
        assert router.get_available_sources() == ["secondary"]

    def test_is_source_available(self):
        cb = CircuitBreaker("primary")
        router = FailoverRouter({"primary": cb})
        assert router.is_source_available("primary") is True
        cb._state.state = CircuitState.OPEN
        assert router.is_source_available("primary") is False

    def test_find_fallback_prefers_closed(self):
        cb_primary = CircuitBreaker("primary")
        cb_secondary = CircuitBreaker("secondary")
        cb_secondary._state.state = CircuitState.HALF_OPEN
        cb_primary._state.state = CircuitState.OPEN
        router = FailoverRouter({"primary": cb_primary, "secondary": cb_secondary})
        assert router._find_fallback("primary") == "secondary"

    def test_unknown_source(self):
        router = FailoverRouter({})
        assert router.get_preferred_source("unknown") == "unknown"
        assert router.is_source_available("unknown") is False


class TestSwitchRules:
    def test_should_use_source(self):
        rules = SwitchRules(trust_score_threshold=0.80, latency_threshold_ms=500.0)
        assert rules.should_use_source(trust_score=0.90, latency_ms=100.0) is True
        assert rules.should_use_source(trust_score=0.70, latency_ms=100.0) is False
        assert rules.should_use_source(trust_score=0.90, latency_ms=600.0) is False

    def test_should_failover(self):
        rules = SwitchRules(trust_score_threshold=0.80, latency_threshold_ms=500.0)
        assert rules.should_failover(trust_score=0.90, latency_ms=100.0) is False
        assert rules.should_failover(trust_score=0.70, latency_ms=100.0) is True
        assert rules.should_failover(trust_score=0.90, latency_ms=600.0) is True


class TestDecisionEngine:
    def test_decide_use_source(self):
        engine = DecisionEngine(
            source_ids=["primary", "secondary"],
            switch_rules=SwitchRules(trust_score_threshold=0.80, latency_threshold_ms=500.0),
        )
        request = DecisionRequest(source_id="primary", trust_score=0.95, latency_ms=100.0)
        result = engine.decide(request)
        assert result.action == DecisionAction.USE_SOURCE
        assert result.target_source == "primary"

    def test_decide_failover_on_threshold(self):
        engine = DecisionEngine(
            source_ids=["primary", "secondary"],
            switch_rules=SwitchRules(trust_score_threshold=0.80, latency_threshold_ms=500.0),
        )
        request = DecisionRequest(source_id="primary", trust_score=0.50, latency_ms=100.0)
        result = engine.decide(request)
        assert result.action == DecisionAction.FAILOVER
        assert result.target_source == "secondary"

    def test_decide_failover_on_cb_open(self):
        engine = DecisionEngine(
            source_ids=["primary", "secondary"],
            switch_rules=SwitchRules(trust_score_threshold=0.80, latency_threshold_ms=500.0),
        )
        engine._cbs["primary"]._state.state = CircuitState.OPEN
        request = DecisionRequest(source_id="primary", trust_score=0.95, latency_ms=100.0)
        result = engine.decide(request)
        assert result.action == DecisionAction.FAILOVER
        assert result.target_source == "secondary"

    def test_decide_skip_unknown_source(self):
        engine = DecisionEngine(
            source_ids=["primary"],
            switch_rules=SwitchRules(trust_score_threshold=0.80, latency_threshold_ms=500.0),
        )
        request = DecisionRequest(source_id="unknown", trust_score=0.95, latency_ms=100.0)
        result = engine.decide(request)
        assert result.action == DecisionAction.SKIP

    def test_decide_skip_all_sources_unavailable(self):
        engine = DecisionEngine(
            source_ids=["primary"],
            switch_rules=SwitchRules(trust_score_threshold=0.80, latency_threshold_ms=500.0),
            alert_manager=AlertManager(),
        )
        engine._cbs["primary"]._state.state = CircuitState.OPEN
        request = DecisionRequest(source_id="primary", trust_score=0.95, latency_ms=100.0)
        result = engine.decide(request)
        assert result.action == DecisionAction.SKIP

    def test_decide_retry_no_fallback(self):
        engine = DecisionEngine(
            source_ids=["primary"],
            switch_rules=SwitchRules(trust_score_threshold=0.80, latency_threshold_ms=500.0),
        )
        request = DecisionRequest(source_id="primary", trust_score=0.50, latency_ms=100.0)
        result = engine.decide(request)
        assert result.action == DecisionAction.RETRY

    def test_decide_with_health_probe(self):
        engine = DecisionEngine(
            source_ids=["primary"],
            switch_rules=SwitchRules(trust_score_threshold=0.80, latency_threshold_ms=500.0),
        )
        probe = HealthProbeResult(
            source_id="primary",
            status=ProbeStatus.HEALTHY,
            latency_ms=50.0,
            checked_at=time.time(),
        )
        request = DecisionRequest(source_id="primary", trust_score=0.95, latency_ms=100.0, health_probe=probe)
        result = engine.decide(request)
        assert result.action == DecisionAction.USE_SOURCE

    def test_update_source_changes_state(self):
        engine = DecisionEngine(
            source_ids=["primary"],
            switch_rules=SwitchRules(trust_score_threshold=0.80, latency_threshold_ms=500.0),
        )
        for _ in range(5):
            probe = HealthProbeResult(
                source_id="primary",
                status=ProbeStatus.UNREACHABLE,
                latency_ms=100.0,
                checked_at=time.time(),
            )
            engine.update_source("primary", probe)
        assert engine.get_cb_state("primary") == CircuitState.OPEN

    def test_persist_and_restore(self, tmp_path):
        path = str(tmp_path / "cb_state.json")
        store = CBStateStore(persist_path=path)

        engine1 = DecisionEngine(
            source_ids=["primary"],
            state_store=store,
            switch_rules=SwitchRules(trust_score_threshold=0.80, latency_threshold_ms=500.0),
        )
        engine1._cbs["primary"]._state.state = CircuitState.OPEN
        engine1.persist_all_states()

        engine2 = DecisionEngine(
            source_ids=["primary"],
            state_store=store,
            switch_rules=SwitchRules(trust_score_threshold=0.80, latency_threshold_ms=500.0),
        )
        assert engine2.get_cb_state("primary") == CircuitState.OPEN

    def test_get_available_sources(self):
        engine = DecisionEngine(
            source_ids=["primary", "secondary"],
            switch_rules=SwitchRules(trust_score_threshold=0.80, latency_threshold_ms=500.0),
        )
        engine._cbs["primary"]._state.state = CircuitState.OPEN
        assert engine.get_available_sources() == ["secondary"]

    def test_reset_source(self):
        engine = DecisionEngine(
            source_ids=["primary"],
            switch_rules=SwitchRules(trust_score_threshold=0.80, latency_threshold_ms=500.0),
        )
        engine._cbs["primary"]._state.state = CircuitState.OPEN
        engine.reset_source("primary")
        assert engine.get_cb_state("primary") == CircuitState.CLOSED

    def test_alert_manager_called_on_failover(self):
        alerts = []
        am = AlertManager()
        am.register_handler(lambda a: alerts.append(a))
        engine = DecisionEngine(
            source_ids=["primary", "secondary"],
            switch_rules=SwitchRules(trust_score_threshold=0.80, latency_threshold_ms=500.0),
            alert_manager=am,
        )
        request = DecisionRequest(source_id="primary", trust_score=0.50, latency_ms=100.0)
        engine.decide(request)
        failover_alerts = [a for a in alerts if a["type"] == "failover"]
        assert len(failover_alerts) == 1
        assert failover_alerts[0]["from_source"] == "primary"
        assert failover_alerts[0]["to_source"] == "secondary"
