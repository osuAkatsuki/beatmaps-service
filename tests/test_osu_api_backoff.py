import time
import unittest
from unittest.mock import patch

import httpx

from app.adapters import osu_api_backoff
from app.adapters.osu_api_backoff import CircuitState
from app.adapters.osu_api_backoff import OsuApiBackoff
from app.adapters.osu_api_backoff import OsuApiBackoffError


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

            mock_time.monotonic.return_value = started_at + 3601
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

            mock_time.monotonic.return_value = started_at + 3601
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

            mock_time.monotonic.return_value = started_at + 3601
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

            mock_time.monotonic.return_value = started_at + 3601
            backoff.raise_if_unavailable(upstream="osu! API v1")
            backoff.record_failure(upstream="osu! API v1", endpoint="get_beatmaps")

            self.assertEqual(backoff.state, CircuitState.OPEN)
            with self.assertRaises(OsuApiBackoffError):
                backoff.raise_if_unavailable(upstream="osu! API v1")


if __name__ == "__main__":
    unittest.main()
