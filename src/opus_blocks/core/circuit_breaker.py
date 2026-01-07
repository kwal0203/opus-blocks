import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field

from opus_blocks.core.config import settings


class CircuitBreakerOpen(RuntimeError):
    pass


@dataclass
class CircuitBreaker:
    failure_threshold: int
    window_seconds: int
    cooldown_seconds: int
    enabled: bool = True
    now_fn: Callable[[], float] = time.monotonic
    failures: deque[float] = field(default_factory=deque)
    opened_at: float | None = None

    def _prune(self, now: float) -> None:
        while self.failures and now - self.failures[0] > self.window_seconds:
            self.failures.popleft()

    def allow_request(self) -> None:
        if not self.enabled:
            return
        now = self.now_fn()
        if self.opened_at is not None:
            if now - self.opened_at < self.cooldown_seconds:
                raise CircuitBreakerOpen("Circuit breaker is open")
            self.opened_at = None
            self.failures.clear()
        self._prune(now)

    def record_failure(self) -> None:
        if not self.enabled:
            return
        now = self.now_fn()
        self._prune(now)
        self.failures.append(now)
        if len(self.failures) >= self.failure_threshold:
            self.opened_at = now

    def record_success(self) -> None:
        if not self.enabled:
            return
        now = self.now_fn()
        self._prune(now)


_llm_breaker = CircuitBreaker(
    failure_threshold=settings.circuit_breaker_failure_threshold,
    window_seconds=settings.circuit_breaker_window_seconds,
    cooldown_seconds=settings.circuit_breaker_cooldown_seconds,
    enabled=settings.circuit_breaker_enabled,
)


def get_llm_circuit_breaker() -> CircuitBreaker:
    return _llm_breaker
