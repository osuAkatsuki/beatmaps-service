import logging
import random
from datetime import datetime
from typing import Any

import httpx
from pydantic import BaseModel

from app import settings
from app.common_models import GameMode

osu_api_v1_http_client = httpx.AsyncClient(
    base_url="https://old.ppy.sh/api/",
    timeout=httpx.Timeout(15),
)


class Beatmap(BaseModel):
    approved: int
    submit_date: datetime
    approved_date: datetime | None
    last_update: datetime
    artist: str
    beatmap_id: int
    beatmapset_id: int
    bpm: float | None
    creator: str
    creator_id: int
    difficultyrating: float
    diff_aim: float | None
    diff_speed: float | None
    diff_size: float
    diff_overall: float
    diff_approach: float
    diff_drain: float
    hit_length: int
    source: str
    genre_id: int
    language_id: int
    title: str
    total_length: int
    version: str
    file_md5: str
    mode: GameMode
    tags: str
    favourite_count: int
    rating: float
    playcount: int
    passcount: int
    count_normal: int
    count_slider: int
    count_spinner: int
    max_combo: int | None
    storyboard: int
    video: int
    download_unavailable: int
    audio_unavailable: int


async def fetch_one_beatmap(
    *,
    beatmap_id: int | None = None,
    beatmap_md5: str | None = None,
) -> Beatmap | None:
    assert [beatmap_id, beatmap_md5].count(None) == 1

    osu_api_response_data: list[dict[str, Any]] | None = None
    try:
        response = await osu_api_v1_http_client.get(
            "get_beatmaps",
            params={
                "k": random.choice(settings.OSU_API_V1_API_KEYS_POOL),
                **({"b": beatmap_id} if beatmap_id else {"h": beatmap_md5}),
            },
        )
        if response.status_code == 404:
            return None
        if response.status_code == 403:
            raise ValueError("osu api is down") from None
        response.raise_for_status()
        osu_api_response_data = response.json()
        if osu_api_response_data == []:
            return None
        assert osu_api_response_data is not None
        return Beatmap(**osu_api_response_data[0])
    except Exception:
        logging.exception(
            "Failed to fetch beatmap from osu! API v1",
            extra={
                "beatmap_id": beatmap_id,
                "osu_api_response_data": osu_api_response_data,
            },
        )
        raise
