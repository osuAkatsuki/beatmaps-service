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


TARGET_LATENCY_MS = 500


async def get_mirror_score(mirror_name: str) -> float:
    """Get a score for a mirror based on recent requests. Higher is better."""
    query = """\
        SELECT success, started_at, ended_at
        FROM beatmap_mirror_requests
        WHERE started_at > NOW() - INTERVAL 1 HOUR
        AND mirror_name = :mirror_name
        ORDER BY started_at DESC
    """
    mirror_requests = [
        BeatmapMirrorRequest(**dict(rec._mapping))
        for rec in await state.database.fetch_all(
            query=query,
            values={"mirror_name": mirror_name},
        )
    ]
    if not mirror_requests:
        return 0

    score = 0
    for mirror_request in mirror_requests:
        if mirror_request.success:
            # successes are good, especially if they're fast
            # 0-1 depending on latency vs. target latency
            score += (
                1
                - (
                    (
                        mirror_request.ended_at - mirror_request.started_at
                    ).total_seconds()
                    * 1000
                )
                / TARGET_LATENCY_MS
            )

        else:
            # failures are very bad
            score -= 10

    return score


async def log_beatmap_mirror_request(request: BeatmapMirrorRequest) -> None:
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
