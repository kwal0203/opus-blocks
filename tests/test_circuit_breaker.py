import pytest

from opus_blocks.core.circuit_breaker import CircuitBreaker, CircuitBreakerOpen


def test_circuit_breaker_opens_after_threshold() -> None:
    now = 0.0

    def _now() -> float:
        return now

    breaker = CircuitBreaker(
        failure_threshold=2,
        window_seconds=60,
        cooldown_seconds=30,
        now_fn=_now,
    )

    breaker.record_failure()
    now += 1
    breaker.record_failure()

    with pytest.raises(CircuitBreakerOpen):
        breaker.allow_request()


def test_circuit_breaker_recovers_after_cooldown() -> None:
    now = 0.0

    def _now() -> float:
        return now

    breaker = CircuitBreaker(
        failure_threshold=1,
        window_seconds=60,
        cooldown_seconds=10,
        now_fn=_now,
    )

    breaker.record_failure()
    with pytest.raises(CircuitBreakerOpen):
        breaker.allow_request()

    now += 11
    breaker.allow_request()
