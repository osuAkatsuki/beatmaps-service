import enum
import logging
import threading
import time
from datetime import datetime
from datetime import timezone
from email.utils import parsedate_to_datetime

import httpx

RATE_LIMIT_STATUS_CODES = {403, 429}
DEFAULT_FAILURE_COOLDOWN_SECONDS = 10
DEFAULT_RATE_LIMIT_COOLDOWN_SECONDS = 60
DEFAULT_OSU_API_REQUESTS_PER_MINUTE = 600
DEFAULT_OSU_API_BURST_SIZE = 60

logger = logging.getLogger(__name__)


class CircuitState(str, enum.Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class OsuApiBackoffError(RuntimeError):
    pass


class OsuApiRateLimiter:
    def __init__(
        self,
        *,
        requests_per_minute: float = DEFAULT_OSU_API_REQUESTS_PER_MINUTE,
        burst_size: float = DEFAULT_OSU_API_BURST_SIZE,
    ) -> None:
        if requests_per_minute <= 0:
            raise ValueError("requests_per_minute must be positive")
        if burst_size <= 0:
            raise ValueError("burst_size must be positive")

        self._tokens_per_second = requests_per_minute / 60
        self._bucket_size = burst_size
        self._tokens = burst_size
        self._last_refill_at = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self) -> float:
        with self._lock:
            self._refill()
            if self._tokens >= 1:
                self._tokens -= 1
                return 0

            return (1 - self._tokens) / self._tokens_per_second

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill_at
        self._tokens = min(
            self._bucket_size,
            self._tokens + elapsed * self._tokens_per_second,
        )
        self._last_refill_at = now


class OsuApiBackoff:
    def __init__(
        self,
        *,
        failure_threshold: int = 3,
        failure_cooldown_seconds: float = DEFAULT_FAILURE_COOLDOWN_SECONDS,
        rate_limiter: OsuApiRateLimiter | None = None,
    ) -> None:
        self._failure_threshold = failure_threshold
        self._failure_cooldown_seconds = failure_cooldown_seconds
        self._rate_limiter = rate_limiter

        self._state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._opened_at = 0.0
        self._cooldown_seconds = failure_cooldown_seconds
        self._probe_in_flight = False
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            return self._evaluate_state()

    def raise_if_unavailable(self, *, upstream: str) -> None:
        with self._lock:
            state = self._evaluate_state()
            if state == CircuitState.CLOSED:
                allow_canary = False

            elif state == CircuitState.HALF_OPEN and not self._probe_in_flight:
                self._probe_in_flight = True
                allow_canary = True

            else:
                seconds_remaining = 0
                if self._state == CircuitState.OPEN:
                    seconds_remaining = max(
                        0,
                        int(self._cooldown_seconds - self._elapsed_since_opened()),
                    )
                raise OsuApiBackoffError(
                    f"{upstream} is backing off for {seconds_remaining}s",
                )

        try:
            self._raise_if_rate_limited(upstream=upstream)
        except OsuApiBackoffError:
            if allow_canary:
                with self._lock:
                    if self._state == CircuitState.HALF_OPEN:
                        self._probe_in_flight = False
            raise

        if allow_canary:
            logger.info(
                "Allowing osu! API canary request",
                extra={"upstream": upstream, "circuit_state": CircuitState.HALF_OPEN},
            )

    def record_success(self, *, upstream: str, endpoint: str) -> None:
        with self._lock:
            previous_state = self._state
            self._state = CircuitState.CLOSED
            self._consecutive_failures = 0
            self._opened_at = 0.0
            self._cooldown_seconds = self._failure_cooldown_seconds
            self._probe_in_flight = False

        if previous_state == CircuitState.HALF_OPEN:
            logger.info(
                "Closed osu! API circuit after successful canary request",
                extra={
                    "upstream": upstream,
                    "endpoint": endpoint,
                    "previous_state": previous_state,
                    "circuit_state": CircuitState.CLOSED,
                },
            )

    def record_failure(
        self,
        *,
        upstream: str,
        endpoint: str,
        cooldown_seconds: float | None = None,
        force_open: bool = False,
    ) -> None:
        cooldown_seconds = cooldown_seconds or self._failure_cooldown_seconds

        with self._lock:
            self._consecutive_failures += 1
            should_open = (
                force_open
                or self._state == CircuitState.HALF_OPEN
                or self._consecutive_failures >= self._failure_threshold
            )
            if not should_open:
                return

            previous_state = self._state
            self._state = CircuitState.OPEN
            self._opened_at = time.monotonic()
            self._cooldown_seconds = cooldown_seconds
            self._probe_in_flight = False

        logger.warning(
            "Opened osu! API circuit",
            extra={
                "upstream": upstream,
                "endpoint": endpoint,
                "previous_state": previous_state,
                "circuit_state": CircuitState.OPEN,
                "consecutive_failures": self._consecutive_failures,
                "cooldown_seconds": cooldown_seconds,
            },
        )

    def apply_if_rate_limited(
        self,
        response: httpx.Response,
        *,
        upstream: str,
        endpoint: str,
    ) -> None:
        if response.status_code not in RATE_LIMIT_STATUS_CODES:
            return

        cooldown_seconds = _get_rate_limit_cooldown_seconds(response)
        self.record_failure(
            upstream=upstream,
            endpoint=endpoint,
            cooldown_seconds=cooldown_seconds,
            force_open=True,
        )
        raise OsuApiBackoffError(
            f"{upstream} returned {response.status_code}; backing off",
        )

    def _evaluate_state(self) -> CircuitState:
        if self._state != CircuitState.OPEN:
            return self._state

        if self._elapsed_since_opened() < self._cooldown_seconds:
            return self._state

        self._state = CircuitState.HALF_OPEN
        self._probe_in_flight = False
        logger.info(
            "Transitioned osu! API circuit to half-open",
            extra={
                "circuit_state": CircuitState.HALF_OPEN,
                "cooldown_seconds": self._cooldown_seconds,
            },
        )
        return self._state

    def _elapsed_since_opened(self) -> float:
        return time.monotonic() - self._opened_at

    def _raise_if_rate_limited(self, *, upstream: str) -> None:
        if self._rate_limiter is None:
            return

        seconds_until_available = self._rate_limiter.acquire()
        if seconds_until_available == 0:
            return

        logger.info(
            "Skipped osu! API request because local rate limit is exhausted",
            extra={
                "upstream": upstream,
                "seconds_until_available": seconds_until_available,
            },
        )
        raise OsuApiBackoffError(
            f"{upstream} local rate limit exhausted; retry in "
            f"{seconds_until_available:.1f}s",
        )


def _get_rate_limit_cooldown_seconds(response: httpx.Response) -> int:
    retry_after = response.headers.get("Retry-After")
    if retry_after is None:
        return DEFAULT_RATE_LIMIT_COOLDOWN_SECONDS

    try:
        return max(1, int(retry_after))
    except ValueError:
        retry_at = _parse_retry_after_datetime(retry_after)
        if retry_at is None:
            return DEFAULT_RATE_LIMIT_COOLDOWN_SECONDS

        return max(1, int((retry_at - datetime.now(timezone.utc)).total_seconds()))


def _parse_retry_after_datetime(retry_after: str) -> datetime | None:
    try:
        retry_at = parsedate_to_datetime(retry_after)
    except (TypeError, ValueError):
        return None

    if retry_at.tzinfo is None:
        retry_at = retry_at.replace(tzinfo=timezone.utc)
    return retry_at


osu_api_rate_limiter = OsuApiRateLimiter()
