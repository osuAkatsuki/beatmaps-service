import time
import unittest
from unittest.mock import patch

import httpx

from app.adapters import osu_api_backoff
from app.adapters.osu_api_backoff import CircuitState
from app.adapters.osu_api_backoff import OsuApiBackoff
from app.adapters.osu_api_backoff import OsuApiBackoffError
from app.adapters.osu_api_backoff import OsuApiRateLimiter


class OsuApiBackoffTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._logger_disabled = osu_api_backoff.logger.disabled
        osu_api_backoff.logger.disabled = True

    def tearDown(self) -> None:
        osu_api_backoff.logger.disabled = self._logger_disabled

    def test_rate_limit_response_opens_circuit(self) -> None:
        backoff = OsuApiBackoff()
        response = httpx.Response(403)

        with self.assertRaises(OsuApiBackoffError):
            backoff.apply_if_rate_limited(
                response,
                upstream="osu! API v1",
                endpoint="get_beatmaps",
            )

        self.assertEqual(backoff.state, CircuitState.OPEN)
        with self.assertRaises(OsuApiBackoffError):
            backoff.raise_if_unavailable(upstream="osu! API v1")

    def test_local_rate_limiter_caps_outbound_requests(self) -> None:
        limiter = OsuApiRateLimiter(requests_per_minute=60, burst_size=1)
        backoff = OsuApiBackoff(rate_limiter=limiter)
        started_at = time.monotonic()

        with patch("app.adapters.osu_api_backoff.time") as mock_time:
            mock_time.monotonic.return_value = started_at
            backoff.raise_if_unavailable(upstream="osu! API v1")

            with self.assertRaises(OsuApiBackoffError) as exc:
                backoff.raise_if_unavailable(upstream="osu! API v1")

            self.assertIn("local rate limit exhausted", str(exc.exception))

            mock_time.monotonic.return_value = started_at + 1
            backoff.raise_if_unavailable(upstream="osu! API v1")

    def test_shared_rate_limiter_is_used_across_backoffs(self) -> None:
        limiter = OsuApiRateLimiter(requests_per_minute=60, burst_size=1)
        v1_backoff = OsuApiBackoff(rate_limiter=limiter)
        v2_backoff = OsuApiBackoff(rate_limiter=limiter)
        started_at = time.monotonic()

        with patch("app.adapters.osu_api_backoff.time") as mock_time:
            mock_time.monotonic.return_value = started_at
            v1_backoff.raise_if_unavailable(upstream="osu! API v1")

            with self.assertRaises(OsuApiBackoffError):
                v2_backoff.raise_if_unavailable(upstream="osu! API v2")

    def test_generic_failures_use_short_cooldown(self) -> None:
        backoff = OsuApiBackoff(failure_threshold=1)
        started_at = time.monotonic()

        with patch("app.adapters.osu_api_backoff.time") as mock_time:
            mock_time.monotonic.return_value = started_at
            backoff.record_failure(upstream="osu! API v1", endpoint="get_beatmaps")
            self.assertEqual(backoff.state, CircuitState.OPEN)

            mock_time.monotonic.return_value = started_at + 9
            self.assertEqual(backoff.state, CircuitState.OPEN)

            mock_time.monotonic.return_value = started_at + 10
            self.assertEqual(backoff.state, CircuitState.HALF_OPEN)

    def test_skipped_calls_do_not_extend_cooldown(self) -> None:
        backoff = OsuApiBackoff()
        started_at = time.monotonic()

        with patch("app.adapters.osu_api_backoff.time") as mock_time:
            mock_time.monotonic.return_value = started_at
            with self.assertRaises(OsuApiBackoffError):
                backoff.apply_if_rate_limited(
                    httpx.Response(429),
                    upstream="osu! API v2",
                    endpoint="beatmapsets/search",
                )

            mock_time.monotonic.return_value = started_at + 10
            for _ in range(5):
                with self.assertRaises(OsuApiBackoffError):
                    backoff.raise_if_unavailable(upstream="osu! API v2")

            mock_time.monotonic.return_value = started_at + 61
            self.assertEqual(backoff.state, CircuitState.HALF_OPEN)

    def test_zero_remaining_rate_limit_header_opens_circuit(self) -> None:
        backoff = OsuApiBackoff()

        backoff.record_rate_limit_headers(
            httpx.Response(
                200,
                headers={
                    "X-Ratelimit-Limit": "1200",
                    "X-Ratelimit-Remaining": "0",
                },
            ),
            upstream="osu! API v2",
            endpoint="beatmaps",
        )

        self.assertEqual(backoff.state, CircuitState.OPEN)
        with self.assertRaises(OsuApiBackoffError):
            backoff.raise_if_unavailable(upstream="osu! API v2")

    def test_positive_remaining_rate_limit_header_does_not_open_circuit(self) -> None:
        backoff = OsuApiBackoff()

        backoff.record_rate_limit_headers(
            httpx.Response(
                200,
                headers={
                    "X-Ratelimit-Limit": "1200",
                    "X-Ratelimit-Remaining": "1",
                },
            ),
            upstream="osu! API v2",
            endpoint="beatmaps",
        )

        self.assertEqual(backoff.state, CircuitState.CLOSED)

    def test_rate_limit_reset_header_controls_cooldown(self) -> None:
        backoff = OsuApiBackoff()
        started_at = time.monotonic()

        with patch("app.adapters.osu_api_backoff.time") as mock_time:
            mock_time.monotonic.return_value = started_at
            mock_time.time.return_value = 1000
            backoff.record_rate_limit_headers(
                httpx.Response(
                    200,
                    headers={
                        "X-Ratelimit-Remaining": "0",
                        "X-Ratelimit-Reset": "1030",
                    },
                ),
                upstream="osu! API v2",
                endpoint="beatmaps",
            )

            mock_time.monotonic.return_value = started_at + 29
            self.assertEqual(backoff.state, CircuitState.OPEN)

            mock_time.monotonic.return_value = started_at + 30
            self.assertEqual(backoff.state, CircuitState.HALF_OPEN)

    def test_rate_limit_response_uses_reset_header_without_retry_after(self) -> None:
        backoff = OsuApiBackoff()
        started_at = time.monotonic()

        with patch("app.adapters.osu_api_backoff.time") as mock_time:
            mock_time.monotonic.return_value = started_at
            mock_time.time.return_value = 1000
            with self.assertRaises(OsuApiBackoffError):
                backoff.apply_if_rate_limited(
                    httpx.Response(429, headers={"X-Ratelimit-Reset": "1030"}),
                    upstream="osu! API v2",
                    endpoint="beatmaps",
                )

            mock_time.monotonic.return_value = started_at + 29
            self.assertEqual(backoff.state, CircuitState.OPEN)

            mock_time.monotonic.return_value = started_at + 30
            self.assertEqual(backoff.state, CircuitState.HALF_OPEN)

    def test_in_flight_success_does_not_close_open_circuit(self) -> None:
        backoff = OsuApiBackoff()

        with self.assertRaises(OsuApiBackoffError):
            backoff.apply_if_rate_limited(
                httpx.Response(429),
                upstream="osu! API v2",
                endpoint="beatmaps",
            )

        backoff.record_success(upstream="osu! API v2", endpoint="beatmaps")

        self.assertEqual(backoff.state, CircuitState.OPEN)
        with self.assertRaises(OsuApiBackoffError):
            backoff.raise_if_unavailable(upstream="osu! API v2")

    def test_duplicate_in_flight_failures_do_not_extend_cooldown(self) -> None:
        backoff = OsuApiBackoff()
        started_at = time.monotonic()

        with patch("app.adapters.osu_api_backoff.time") as mock_time:
            mock_time.monotonic.return_value = started_at
            with self.assertRaises(OsuApiBackoffError):
                backoff.apply_if_rate_limited(
                    httpx.Response(429),
                    upstream="osu! API v2",
                    endpoint="beatmaps",
                )

            mock_time.monotonic.return_value = started_at + 30
            with self.assertRaises(OsuApiBackoffError):
                backoff.apply_if_rate_limited(
                    httpx.Response(429),
                    upstream="osu! API v2",
                    endpoint="beatmaps",
                )

            mock_time.monotonic.return_value = started_at + 61
            self.assertEqual(backoff.state, CircuitState.HALF_OPEN)

    def test_only_one_canary_is_allowed_in_half_open(self) -> None:
        backoff = OsuApiBackoff()
        started_at = time.monotonic()

        with patch("app.adapters.osu_api_backoff.time") as mock_time:
            mock_time.monotonic.return_value = started_at
            with self.assertRaises(OsuApiBackoffError):
                backoff.apply_if_rate_limited(
                    httpx.Response(403),
                    upstream="osu! API v1",
                    endpoint="get_beatmaps",
                )

            mock_time.monotonic.return_value = started_at + 61
            backoff.raise_if_unavailable(upstream="osu! API v1")
            with self.assertRaises(OsuApiBackoffError):
                backoff.raise_if_unavailable(upstream="osu! API v1")

    def test_successful_canary_closes_circuit(self) -> None:
        backoff = OsuApiBackoff()
        started_at = time.monotonic()

        with patch("app.adapters.osu_api_backoff.time") as mock_time:
            mock_time.monotonic.return_value = started_at
            with self.assertRaises(OsuApiBackoffError):
                backoff.apply_if_rate_limited(
                    httpx.Response(403),
                    upstream="osu! API v1",
                    endpoint="get_beatmaps",
                )

            mock_time.monotonic.return_value = started_at + 61
            backoff.raise_if_unavailable(upstream="osu! API v1")
            backoff.record_success(upstream="osu! API v1", endpoint="get_beatmaps")

        self.assertEqual(backoff.state, CircuitState.CLOSED)
        backoff.raise_if_unavailable(upstream="osu! API v1")

    def test_failed_canary_reopens_circuit(self) -> None:
        backoff = OsuApiBackoff()
        started_at = time.monotonic()

        with patch("app.adapters.osu_api_backoff.time") as mock_time:
            mock_time.monotonic.return_value = started_at
            with self.assertRaises(OsuApiBackoffError):
                backoff.apply_if_rate_limited(
                    httpx.Response(403),
                    upstream="osu! API v1",
                    endpoint="get_beatmaps",
                )

            mock_time.monotonic.return_value = started_at + 61
            backoff.raise_if_unavailable(upstream="osu! API v1")
            backoff.record_failure(upstream="osu! API v1", endpoint="get_beatmaps")

            self.assertEqual(backoff.state, CircuitState.OPEN)
            with self.assertRaises(OsuApiBackoffError):
                backoff.raise_if_unavailable(upstream="osu! API v1")


if __name__ == "__main__":
    unittest.main()
