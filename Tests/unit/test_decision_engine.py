from __future__ import annotations

import time

import pytest

from DecisionEngine.CircuitBreaker import CircuitBreaker, CircuitState
from errors import CircuitBreakerError, CircuitBreakerTripped


class TestCircuitBreakerCreation:
    def test_default_parameters(self):
        cb = CircuitBreaker("source-a")
        assert cb.source_id == "source-a"
        assert cb.failure_threshold == 5
        assert cb.success_threshold == 2
        assert cb.recovery_timeout == 30.0
        assert cb.state == CircuitState.CLOSED

    def test_custom_parameters(self):
        cb = CircuitBreaker("source-b", failure_threshold=3, success_threshold=3, recovery_timeout=60.0)
        assert cb.failure_threshold == 3
        assert cb.success_threshold == 3
        assert cb.recovery_timeout == 60.0

    def test_invalid_failure_threshold(self):
        with pytest.raises(ValueError, match="failure_threshold"):
            CircuitBreaker("x", failure_threshold=0)

    def test_invalid_success_threshold(self):
        with pytest.raises(ValueError, match="success_threshold"):
            CircuitBreaker("x", success_threshold=0)

    def test_invalid_timeout(self):
        with pytest.raises(ValueError, match="recovery_timeout"):
            CircuitBreaker("x", recovery_timeout=0)


class TestCircuitBreakerClosedState:
    def test_successful_call_stays_closed(self):
        cb = CircuitBreaker("source-a", failure_threshold=3)
        result = cb.call(lambda: "ok")
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED

    def test_failure_increments_counter(self):
        cb = CircuitBreaker("source-a", failure_threshold=3)

        def fail():
            raise ValueError("boom")

        with pytest.raises(CircuitBreakerError):
            cb.call(fail)
        assert cb.state == CircuitState.CLOSED

    def test_failure_threshold_reached_trips_to_open(self):
        cb = CircuitBreaker("source-a", failure_threshold=3)

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
        cb = CircuitBreaker("source-a", failure_threshold=3)

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
        cb = CircuitBreaker("source-a", failure_threshold=1, recovery_timeout=999)

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
        cb = CircuitBreaker("source-a", failure_threshold=1, recovery_timeout=0.05)

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
        cb = CircuitBreaker("source-a", failure_threshold=1)

        def fail():
            raise ValueError("boom")

        with pytest.raises(CircuitBreakerError):
            cb.call(fail)
        assert cb.state == CircuitState.OPEN

        cb.reset()
        assert cb.state == CircuitState.CLOSED


class TestCircuitBreakerHalfOpenState:
    def test_success_threshold_closes_circuit(self):
        cb = CircuitBreaker("source-a", failure_threshold=1, success_threshold=2, recovery_timeout=0.05)

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
        cb = CircuitBreaker("source-a", failure_threshold=1, success_threshold=2, recovery_timeout=0.05)

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


class TestCircuitBreakerErrorPassthrough:
    def test_sync_call_reraises_circuit_breaker_error(self):
        cb = CircuitBreaker("source-a", failure_threshold=5)

        def raise_cb_error():
            raise CircuitBreakerError("original error")

        with pytest.raises(CircuitBreakerError, match="original error"):
            cb.call(raise_cb_error)

    @pytest.mark.asyncio
    async def test_async_call_reraises_circuit_breaker_error(self):
        cb = CircuitBreaker("source-a", failure_threshold=5)

        async def raise_cb_error():
            raise CircuitBreakerError("original error")

        with pytest.raises(CircuitBreakerError, match="original error"):
            await cb.async_call(raise_cb_error)


class TestAsyncCircuitBreaker:
    @pytest.mark.asyncio
    async def test_successful_async_call(self):
        cb = CircuitBreaker("source-a", failure_threshold=3)

        async def ok():
            return "ok"

        result = await cb.async_call(ok)
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_failure_trips_circuit(self):
        cb = CircuitBreaker("source-a", failure_threshold=1)

        async def fail():
            raise RuntimeError("boom")

        with pytest.raises(CircuitBreakerError):
            await cb.async_call(fail)
        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_tripped_rejects_async_call(self):
        cb = CircuitBreaker("source-a", failure_threshold=1, recovery_timeout=999)

        async def fail():
            raise RuntimeError("boom")

        with pytest.raises(CircuitBreakerError):
            await cb.async_call(fail)

        async def ok():
            return "ok"

        with pytest.raises(CircuitBreakerTripped):
            await cb.async_call(ok)
