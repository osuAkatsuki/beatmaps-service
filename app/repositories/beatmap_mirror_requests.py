import math
from datetime import datetime

from pydantic import BaseModel

from app import state

# Give new mirrors a fair shot
# to get their foot in the race
MIRROR_INITIAL_WEIGHT = 100


class BeatmapMirrorScore(BaseModel):
    mirror_name: str
    score: float


async def get_mirror_weight(mirror_name: str) -> int:
    """Give the mirror a weighting based on its latency and failure rate."""
    p75_success_ms_latency = await state.database.fetch_val(
        """\
        WITH request_latencies AS (
            SELECT (ended_at - started_at) * 1000 AS ms_elapsed,
            PERCENT_RANK() OVER (ORDER BY ended_at - started_at) p
            FROM beatmap_mirror_requests
            WHERE started_at > NOW() - INTERVAL 4 HOUR
            AND mirror_name = :mirror_name
            AND success = 1
        )
        SELECT DISTINCT first_value(ms_elapsed) OVER (
            ORDER BY CASE WHEN p <= 0.75 THEN p END DESC
        ) p75_success_ms_latency
        FROM request_latencies
        """,
        {"mirror_name": mirror_name},
    )
    if p75_success_ms_latency is None:
        return MIRROR_INITIAL_WEIGHT

    failure_rate = await state.database.fetch_val(
        """\
        SELECT AVG(success = 0)
        FROM beatmap_mirror_requests
        WHERE started_at > NOW() - INTERVAL 4 HOUR
        AND mirror_name = :mirror_name
        """,
        {"mirror_name": mirror_name},
    )
    if failure_rate is None:
        return MIRROR_INITIAL_WEIGHT

    # https://www.desmos.com/calculator/wxpsjhdby9
    latency_weight = 1000 * math.exp(-1 / 1000 * float(p75_success_ms_latency))
    failure_weight = math.exp(-30 * failure_rate)
    # TODO: integrate `mirror_cache_age` into the weight calculation
    weight = max(1, int(latency_weight * failure_weight))
    return weight


async def create(
    request_url: str,
    api_key_id: str | None,
    mirror_name: str,
    success: bool,
    started_at: datetime,
    ended_at: datetime,
    response_size: int,
    response_error: str | None,
) -> None:
    query = """\
        INSERT INTO beatmap_mirror_requests (
            request_url, api_key_id, mirror_name, success, started_at,
            ended_at, response_size, response_error
        )
        VALUES (
            :request_url, :api_key_id, :mirror_name, :success, :started_at,
            :ended_at, :response_size, :response_error
        )
    """
    await state.database.execute(
        query=query,
        values={
            "request_url": request_url,
            "api_key_id": api_key_id,
            "mirror_name": mirror_name,
            "success": success,
            "started_at": started_at,
            "ended_at": ended_at,
            "response_size": response_size,
            "response_error": response_error,
        },
    )
