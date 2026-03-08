import asyncio
import logging
from abc import ABC
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from typing import ClassVar
from typing import Generic
from typing import TypeVar

import httpx

from app.adapters.osu_mirrors.resilience import MirrorHealth
from app.adapters.osu_mirrors.resilience import TokenBucket
from app.common_models import CheesegullBeatmap
from app.common_models import CheesegullBeatmapset
from app.repositories.beatmap_mirror_requests import MirrorResource

T = TypeVar("T", covariant=True)
_R = TypeVar("_R")

RETRYABLE_STATUSES = frozenset({429, 500, 502, 503})
NOT_FOUND_STATUSES = frozenset({404, 451})

MAX_RETRIES = 1
RETRY_BACKOFF_SECONDS = 1.0
MAX_RESPONSE_BYTES = 100 * 1024 * 1024  # 100 MB


@dataclass
class BeatmapMirrorResponse(Generic[T]):
    data: T
    is_success: bool
    request_url: str | None
    status_code: int | None
    error_message: str | None = None


class AbstractBeatmapMirror(ABC):
    name: ClassVar[str]
    base_url: ClassVar[str]
    supported_resources: ClassVar[set[MirrorResource]]
    requests_per_second: ClassVar[float | None] = None  # Rate limit, if known

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.http_client = httpx.AsyncClient(
            headers={"User-Agent": "Akatsuki-Beatmaps-Service/1.0"},
            timeout=httpx.Timeout(10.0, connect=5.0),
            follow_redirects=True,
        )
        # Initialize health tracking with optional rate limiter
        rate_limiter = None
        if self.requests_per_second is not None:
            rate_limiter = TokenBucket(
                tokens_per_second=self.requests_per_second,
                bucket_size=self.requests_per_second * 2,  # Allow small bursts
            )
        self.health = MirrorHealth(rate_limiter=rate_limiter)
        super().__init__(*args, **kwargs)

    def _extra_headers(self) -> dict[str, str]:
        """Override to add mirror-specific request headers."""
        return {}

    async def _fetch(
        self,
        url: str,
        parse: Callable[[httpx.Response], _R],
        *,
        extra_headers: dict[str, str] | None = None,
        max_response_bytes: int | None = None,
    ) -> BeatmapMirrorResponse[_R | None]:
        """Make an HTTP GET request with retry logic and error handling.

        Retries on transient HTTP errors (429, 500, 502, 503) up to
        MAX_RETRIES times with exponential backoff. Checks upstream
        rate limit headers and applies backpressure to the token bucket.
        Optionally rejects responses exceeding max_response_bytes.
        """
        merged_headers = {**self._extra_headers(), **(extra_headers or {})}
        response: httpx.Response | None = None

        for attempt in range(MAX_RETRIES + 1):
            try:
                response = await self.http_client.get(
                    url,
                    headers=merged_headers or None,
                )
            except Exception as exc:
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_BACKOFF_SECONDS * (attempt + 1))
                    continue
                return BeatmapMirrorResponse(
                    data=None,
                    is_success=False,
                    request_url=None,
                    status_code=None,
                    error_message=str(exc),
                )

            self._check_rate_limit_headers(response)

            if response.status_code in NOT_FOUND_STATUSES:
                return BeatmapMirrorResponse(
                    data=None,
                    is_success=True,
                    request_url=str(response.request.url),
                    status_code=response.status_code,
                )

            if response.status_code in RETRYABLE_STATUSES:
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_BACKOFF_SECONDS * (attempt + 1))
                    continue
                return BeatmapMirrorResponse(
                    data=None,
                    is_success=False,
                    request_url=str(response.request.url),
                    status_code=response.status_code,
                    error_message=f"HTTP {response.status_code} after retries",
                )

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                return BeatmapMirrorResponse(
                    data=None,
                    is_success=False,
                    request_url=str(response.request.url),
                    status_code=response.status_code,
                    error_message=str(exc),
                )

            if max_response_bytes is not None:
                content_length = response.headers.get("content-length")
                if (
                    content_length is not None
                    and int(content_length) > max_response_bytes
                ):
                    return BeatmapMirrorResponse(
                        data=None,
                        is_success=False,
                        request_url=str(response.request.url),
                        status_code=response.status_code,
                        error_message=f"Response too large: {content_length} bytes",
                    )

            try:
                data = parse(response)
            except Exception as exc:
                logging.warning(
                    "Failed to parse mirror response",
                    extra={
                        "mirror_name": self.name,
                        "url": url,
                        "error": str(exc),
                    },
                )
                return BeatmapMirrorResponse(
                    data=None,
                    is_success=False,
                    request_url=str(response.request.url),
                    status_code=response.status_code,
                    error_message=str(exc),
                )

            return BeatmapMirrorResponse(
                data=data,
                is_success=True,
                request_url=str(response.request.url),
                status_code=response.status_code,
            )

        # Unreachable, but satisfies the type checker
        return BeatmapMirrorResponse(
            data=None,
            is_success=False,
            request_url=None,
            status_code=None,
            error_message="All retries exhausted",
        )

    def _check_rate_limit_headers(self, response: httpx.Response) -> None:
        """Check rate limit headers and apply backpressure to token bucket."""
        remaining = response.headers.get("x-ratelimit-remaining")
        if remaining is not None:
            try:
                self.health.apply_rate_limit_pressure(int(remaining))
            except ValueError:
                pass

    async def fetch_one_cheesegull_beatmap(
        self,
        beatmap_id: int,
    ) -> BeatmapMirrorResponse[CheesegullBeatmap | None]:
        """Fetch a cheesegull beatmap from a beatmap mirror."""
        raise NotImplementedError()

    async def fetch_one_cheesegull_beatmapset(
        self,
        beatmapset_id: int,
    ) -> BeatmapMirrorResponse[CheesegullBeatmapset | None]:
        """Fetch a cheesegull beatmapset from a beatmap mirror."""
        raise NotImplementedError()

    async def fetch_beatmap_zip_data(
        self,
        beatmapset_id: int,
    ) -> BeatmapMirrorResponse[bytes | None]:
        """Fetch a beatmap's .osz file content from a beatmap mirror."""
        raise NotImplementedError()

    async def fetch_beatmap_background_image(
        self,
        beatmap_id: int,
    ) -> BeatmapMirrorResponse[bytes | None]:
        """Fetch a beatmap's background image from a beatmap mirror."""
        raise NotImplementedError()
