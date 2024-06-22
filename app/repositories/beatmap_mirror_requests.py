import math
from datetime import datetime

from pydantic import BaseModel

from app import state


class BeatmapMirrorRequest(BaseModel):
    request_url: str
    api_key_id: str | None
    mirror_name: str
    success: bool
    started_at: datetime
    ended_at: datetime
    response_size: int | None
    response_error: str | None


class BeatmapMirrorScore(BaseModel):
    mirror_name: str
    score: float


async def get_mirror_weight(mirror_name: str) -> int:
    """Give the mirror a weighting based on its latency and failure rate."""
    p90_success_ms_latency = await state.database.fetch_val(
        """\
        WITH request_latencies AS (
            SELECT (ended_at - started_at) * 1000 AS ms_elapsed,
            PERCENT_RANK() OVER (ORDER BY ended_at - started_at) p
            FROM beatmap_mirror_requests
            WHERE started_at > NOW() - INTERVAL 1 HOUR
            AND mirror_name = :mirror_name
            AND success = 1
        )
        SELECT DISTINCT first_value(ms_elapsed) OVER (
            ORDER BY CASE WHEN p <= 0.9 THEN p END DESC
        ) p90_success_ms_latency
        FROM request_latencies
        """,
        {"mirror_name": mirror_name},
    )
    if p90_success_ms_latency is None:
        return 1

    failure_rate = await state.database.fetch_val(
        """\
        SELECT AVG(success = 0)
        FROM beatmap_mirror_requests
        WHERE started_at > NOW() - INTERVAL 1 HOUR
        AND mirror_name = :mirror_name
        """,
        {"mirror_name": mirror_name},
    )
    if failure_rate is None:
        return 1

    # https://www.desmos.com/calculator/0am8xnwxyo
    latency_weight = 1000 / math.log(p90_success_ms_latency)
    failure_weight = math.exp(-10 * failure_rate)
    weight = max(1, int(latency_weight * failure_weight))
    return weight


async def create(request: BeatmapMirrorRequest) -> None:
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
    await state.database.execute(query=query, values=request.model_dump())
