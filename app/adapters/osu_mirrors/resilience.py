import time
from dataclasses import dataclass
from dataclasses import field
from enum import StrEnum


class CircuitState(StrEnum):
    CLOSED = "closed"  # Normal operation, requests allowed
    OPEN = "open"  # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing recovery, one request allowed


@dataclass
class CircuitBreaker:
    """
    Circuit breaker pattern implementation.

    Tracks failures and temporarily stops sending requests to a failing backend.
    After a cooldown period, allows a single probe request to test recovery.
    """

    failure_threshold: int = 3
    cooldown_seconds: float = 30.0

    state: CircuitState = field(default=CircuitState.CLOSED)
    consecutive_failures: int = field(default=0)
    opened_at: float | None = field(default=None)

    def record_success(self) -> None:
        """Record a successful request. Resets failure count and closes circuit."""
        self.consecutive_failures = 0
        self.state = CircuitState.CLOSED
        self.opened_at = None

    def record_failure(self) -> None:
        """Record a failed request. Opens circuit if threshold is exceeded."""
        self.consecutive_failures += 1
        if self.consecutive_failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.opened_at = time.time()

    def should_allow_request(self) -> bool:
        """Check if a request should be allowed through the circuit."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if self.opened_at is None:
                return True
            elapsed = time.time() - self.opened_at
            if elapsed >= self.cooldown_seconds:
                # Transition to half-open, allow one probe request
                self.state = CircuitState.HALF_OPEN
                return True
            return False

        # HALF_OPEN: allow the probe request
        return True


@dataclass
class TokenBucket:
    """
    Token bucket rate limiter.

    Allows requests up to a certain rate, with burst capacity.
    Tokens regenerate over time at a fixed rate.
    """

    tokens_per_second: float
    bucket_size: float | None = None  # Max tokens (burst capacity)

    tokens: float = field(init=False)
    last_update: float = field(init=False)

    def __post_init__(self) -> None:
        if self.bucket_size is None:
            self.bucket_size = self.tokens_per_second
        self.tokens = self.bucket_size
        self.last_update = time.time()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(
            self.bucket_size,  # type: ignore[arg-type]
            self.tokens + elapsed * self.tokens_per_second,
        )
        self.last_update = now

    def try_acquire(self, tokens: float = 1.0) -> bool:
        """Try to acquire tokens. Returns True if successful."""
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def time_until_available(self, tokens: float = 1.0) -> float:
        """Returns seconds until the requested tokens will be available."""
        self._refill()
        if self.tokens >= tokens:
            return 0.0
        needed = tokens - self.tokens
        return needed / self.tokens_per_second


@dataclass
class MirrorHealth:
    """
    Tracks health metrics for a single mirror.

    Combines circuit breaker, rate limiting, and latency tracking.
    """

    circuit: CircuitBreaker = field(default_factory=CircuitBreaker)
    rate_limiter: TokenBucket | None = field(default=None)

    # Exponential moving average of successful request latency (seconds)
    latency_ema: float = field(default=1.0)
    latency_ema_alpha: float = field(default=0.3)  # Weight for new observations

    def is_available(self) -> bool:
        """Check if this mirror is available for requests."""
        if not self.circuit.should_allow_request():
            return False
        if self.rate_limiter is not None and not self.rate_limiter.try_acquire():
            return False
        return True

    def record_success(self, latency_seconds: float) -> None:
        """Record a successful request with its latency."""
        self.circuit.record_success()
        # Update EMA: new_ema = alpha * observation + (1 - alpha) * old_ema
        self.latency_ema = (
            self.latency_ema_alpha * latency_seconds
            + (1 - self.latency_ema_alpha) * self.latency_ema
        )

    def record_failure(self) -> None:
        """Record a failed request."""
        self.circuit.record_failure()
