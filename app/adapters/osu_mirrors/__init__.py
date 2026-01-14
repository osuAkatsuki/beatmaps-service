import asyncio
import logging
import time
from collections.abc import Awaitable
from collections.abc import Callable
from datetime import datetime
from typing import TypeVar

from app.adapters.osu_mirrors.backends import AbstractBeatmapMirror
from app.adapters.osu_mirrors.backends import BeatmapMirrorResponse
from app.adapters.osu_mirrors.backends.mino import MinoCentralMirror
from app.adapters.osu_mirrors.backends.mino import MinoSingaporeMirror
from app.adapters.osu_mirrors.backends.mino import MinoUSMirror
from app.adapters.osu_mirrors.backends.nerinyan import NerinyanMirror
from app.adapters.osu_mirrors.backends.osu_direct import OsuDirectMirror
from app.common_models import CheesegullBeatmap
from app.common_models import CheesegullBeatmapset
from app.repositories import beatmap_mirror_requests
from app.repositories.beatmap_mirror_requests import MirrorResource

T = TypeVar("T")

ZIP_FILE_HEADER = b"PK\x03\x04"

# How many mirrors to race simultaneously
HEDGE_COUNT = 2

BEATMAP_MIRRORS: list[AbstractBeatmapMirror] = [
    OsuDirectMirror(),
    MinoCentralMirror(),
    MinoUSMirror(),
    MinoSingaporeMirror(),
    NerinyanMirror(),
    # GatariMirror(),  # Disabled as ratelimit is very low
    # RippleMirror(),  # Disabled as only ranked maps are supported
]


def is_valid_zip_file(content: bytes) -> bool:
    return content.startswith(ZIP_FILE_HEADER)


def get_available_mirrors(
    resource: MirrorResource,
) -> list[AbstractBeatmapMirror]:
    """
    Get mirrors that support the given resource and are currently available.

    Filters by:
    - Resource support
    - Circuit breaker state (not open)
    - Rate limiter (has capacity)

    Returns mirrors sorted by latency EMA (fastest first).
    """
    available = [
        mirror
        for mirror in BEATMAP_MIRRORS
        if resource in mirror.supported_resources and mirror.health.is_available()
    ]
    # Sort by latency (fastest first)
    available.sort(key=lambda m: m.health.latency_ema)
    return available


async def hedged_fetch(
    mirrors: list[AbstractBeatmapMirror],
    fetch_func: Callable[[AbstractBeatmapMirror], Awaitable[BeatmapMirrorResponse[T]]],
    resource: MirrorResource,
    resource_id: int,
    validate_func: Callable[[T], bool] | None = None,
) -> tuple[AbstractBeatmapMirror, BeatmapMirrorResponse[T]] | None:
    """
    Race multiple mirrors and return the first successful response.

    Sends requests to multiple mirrors simultaneously and returns as soon as
    one succeeds. Updates circuit breaker state based on results.

    Args:
        mirrors: List of mirrors to try (should be pre-filtered for availability)
        fetch_func: Async function to call on each mirror
        resource: The type of resource being fetched (for logging)
        resource_id: The ID of the resource being fetched (for logging)
        validate_func: Optional validation function for the response data

    Returns:
        Tuple of (mirror, response) on success, None if all mirrors failed
    """
    if not mirrors:
        logging.warning(
            "No available mirrors for hedged fetch",
            extra={"resource": resource, "resource_id": resource_id},
        )
        return None

    async def fetch_with_tracking(
        mirror: AbstractBeatmapMirror,
    ) -> tuple[AbstractBeatmapMirror, BeatmapMirrorResponse[T], float]:
        started_at = time.time()
        response = await fetch_func(mirror)
        elapsed = time.time() - started_at
        return mirror, response, elapsed

    # Create tasks for all mirrors
    tasks = [
        asyncio.create_task(fetch_with_tracking(mirror))
        for mirror in mirrors[:HEDGE_COUNT]
    ]

    result: tuple[AbstractBeatmapMirror, BeatmapMirrorResponse[T]] | None = None
    pending = set(tasks)

    try:
        while pending:
            done, pending = await asyncio.wait(
                pending,
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in done:
                mirror, response, elapsed = task.result()

                # Log the request for metrics
                await beatmap_mirror_requests.create(
                    request_url=response.request_url or "unavailable",
                    api_key_id=None,
                    mirror_name=mirror.name,
                    success=response.is_success,
                    started_at=datetime.fromtimestamp(time.time() - elapsed),
                    ended_at=datetime.now(),
                    response_status_code=response.status_code,
                    response_size=len(response.data) if response.data else 0,
                    response_error=response.error_message,
                    resource=resource,
                )

                # Validate response if needed
                is_valid = response.is_success
                if is_valid and response.data is not None and validate_func:
                    if not validate_func(response.data):
                        is_valid = False
                        response.is_success = False
                        response.error_message = "Validation failed"

                # Update circuit breaker state
                if is_valid:
                    mirror.health.record_success(elapsed)
                    if response.data is not None:
                        # Found valid data - cancel remaining tasks and return
                        result = (mirror, response)
                        for t in pending:
                            t.cancel()
                        pending = set()
                        break
                else:
                    mirror.health.record_failure()
                    logging.warning(
                        "Mirror request failed",
                        extra={
                            "mirror_name": mirror.name,
                            "resource": resource,
                            "resource_id": resource_id,
                            "status_code": response.status_code,
                            "error": response.error_message,
                            "circuit_state": mirror.health.circuit.state,
                        },
                    )
    finally:
        # Ensure all remaining tasks are cancelled
        for task in pending:
            task.cancel()

    return result


async def fetch_with_fallback(
    resource: MirrorResource,
    resource_id: int,
    fetch_func: Callable[[AbstractBeatmapMirror], Awaitable[BeatmapMirrorResponse[T]]],
    validate_func: Callable[[T], bool] | None = None,
) -> T | None:
    """
    Fetch a resource using hedged requests with fallback.

    First tries racing the top mirrors. If all fail, tries remaining mirrors
    one at a time as a fallback.

    Returns the data on success, None if all mirrors failed.
    """
    available = get_available_mirrors(resource)

    if not available:
        logging.warning(
            "No mirrors available",
            extra={"resource": resource, "resource_id": resource_id},
        )
        return None

    # First, try hedged request with top mirrors
    result = await hedged_fetch(
        mirrors=available[:HEDGE_COUNT],
        fetch_func=fetch_func,
        resource=resource,
        resource_id=resource_id,
        validate_func=validate_func,
    )

    if result is not None:
        mirror, response = result
        logging.debug(
            "Served resource from mirror (hedged)",
            extra={
                "mirror_name": mirror.name,
                "resource": resource,
                "resource_id": resource_id,
                "latency_ema": mirror.health.latency_ema,
            },
        )
        return response.data

    # Hedged request failed, try remaining mirrors sequentially
    for mirror in available[HEDGE_COUNT:]:
        if not mirror.health.is_available():
            continue

        started_at = time.time()
        response = await fetch_func(mirror)
        elapsed = time.time() - started_at

        # Log the request
        await beatmap_mirror_requests.create(
            request_url=response.request_url or "unavailable",
            api_key_id=None,
            mirror_name=mirror.name,
            success=response.is_success,
            started_at=datetime.fromtimestamp(started_at),
            ended_at=datetime.now(),
            response_status_code=response.status_code,
            response_size=len(response.data) if response.data else 0,
            response_error=response.error_message,
            resource=resource,
        )

        # Validate
        is_valid = response.is_success
        if is_valid and response.data is not None and validate_func:
            if not validate_func(response.data):
                is_valid = False

        if is_valid:
            mirror.health.record_success(elapsed)
            if response.data is not None:
                logging.debug(
                    "Served resource from mirror (fallback)",
                    extra={
                        "mirror_name": mirror.name,
                        "resource": resource,
                        "resource_id": resource_id,
                    },
                )
                return response.data
        else:
            mirror.health.record_failure()
            logging.warning(
                "Fallback mirror request failed",
                extra={
                    "mirror_name": mirror.name,
                    "resource": resource,
                    "resource_id": resource_id,
                    "status_code": response.status_code,
                    "error": response.error_message,
                },
            )

    logging.warning(
        "All mirrors failed",
        extra={"resource": resource, "resource_id": resource_id},
    )
    return None


async def fetch_one_cheesegull_beatmap(beatmap_id: int) -> CheesegullBeatmap | None:
    """Fetch a cheesegull beatmap from the fastest available mirror."""
    return await fetch_with_fallback(
        resource=MirrorResource.OSZ_FILE,  # Using OSZ_FILE for compatibility
        resource_id=beatmap_id,
        fetch_func=lambda m: m.fetch_one_cheesegull_beatmap(beatmap_id),
    )


async def fetch_one_cheesegull_beatmapset(
    beatmapset_id: int,
) -> CheesegullBeatmapset | None:
    """Fetch a cheesegull beatmapset from the fastest available mirror."""
    return await fetch_with_fallback(
        resource=MirrorResource.OSZ_FILE,  # Using OSZ_FILE for compatibility
        resource_id=beatmapset_id,
        fetch_func=lambda m: m.fetch_one_cheesegull_beatmapset(beatmapset_id),
    )


async def fetch_beatmap_zip_data(beatmapset_id: int) -> bytes | None:
    """
    Fetch a beatmapset .osz file using hedged requests.

    Races multiple mirrors simultaneously and returns the first valid response.
    Uses circuit breakers to avoid repeatedly hitting failing mirrors.
    """
    return await fetch_with_fallback(
        resource=MirrorResource.OSZ_FILE,
        resource_id=beatmapset_id,
        fetch_func=lambda m: m.fetch_beatmap_zip_data(beatmapset_id),
        validate_func=is_valid_zip_file,
    )


async def fetch_beatmap_background_image(beatmap_id: int) -> bytes | None:
    """
    Fetch a beatmap background image using hedged requests.

    Races multiple mirrors simultaneously and returns the first valid response.
    Uses circuit breakers to avoid repeatedly hitting failing mirrors.
    """
    return await fetch_with_fallback(
        resource=MirrorResource.BACKGROUND_IMAGE,
        resource_id=beatmap_id,
        fetch_func=lambda m: m.fetch_beatmap_background_image(beatmap_id),
    )
