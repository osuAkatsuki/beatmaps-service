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


async def get_active_beatmap_mirror_scores() -> list[BeatmapMirrorScore]:
    query = """\
        SELECT mirror_name, success, started_at, ended_at
        FROM beatmap_mirror_requests
        WHERE started_at > NOW() - INTERVAL 1 HOUR
    """
    mirror_requests = [
        BeatmapMirrorRequest(**dict(rec._mapping))
        for rec in await state.database.fetch_all(query=query)
    ]

    p90_mirror_latency = sorted(
        mirror_request.ended_at - mirror_request.started_at
        for mirror_request in mirror_requests
    )[int(len(mirror_requests) * 0.9)]

    mirror_scores: dict[str, float] = {}

    for mirror_request in mirror_requests:
        if mirror_request.success:
            # successes are good, especially if they're fast
            # 0-1 depending on latency vs. p90 latency
            score = (
                1
                - (mirror_request.ended_at - mirror_request.started_at)
                / p90_mirror_latency
            )

        else:
            # failures are very bad
            score = -10

        mirror_scores[mirror_request.mirror_name] = (
            mirror_scores.get(mirror_request.mirror_name, 0) + score
        )

    return [
        BeatmapMirrorScore(mirror_name=mirror_name, score=score)
        for mirror_name, score in mirror_scores.items()
    ]


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
