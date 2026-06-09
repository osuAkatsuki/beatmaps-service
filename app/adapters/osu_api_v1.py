import logging
import random
from datetime import datetime
from typing import Any

import httpx
from pydantic import BaseModel

from app import settings
from app.adapters.osu_api_backoff import OsuApiBackoff
from app.adapters.osu_api_backoff import OsuApiBackoffError
from app.adapters.osu_api_backoff import osu_api_rate_limiter
from app.common_models import GameMode

osu_api_v1_http_client = httpx.AsyncClient(
    base_url="https://old.ppy.sh/",
    timeout=httpx.Timeout(15),
)
osu_api_v1_backoff = OsuApiBackoff(rate_limiter=osu_api_rate_limiter)


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

    osu_api_v1_backoff.raise_if_unavailable(upstream="osu! API v1")

    osu_api_response_data: list[dict[str, Any]] | None = None
    endpoint = "get_beatmaps"
    try:
        osu_api_v1_key = random.choice(settings.OSU_API_V1_API_KEYS_POOL)
        response = await osu_api_v1_http_client.get(
            "api/get_beatmaps",
            params={
                "k": osu_api_v1_key,
                **({"b": beatmap_id} if beatmap_id else {"h": beatmap_md5}),
            },
        )
        logging.debug(
            "Made request to the v1 osu! api",
            extra={
                "endpoint": "get_beatmaps",
                "api_key_last4": osu_api_v1_key[-4:],
                "authorized": True,
            },
        )
        osu_api_v1_backoff.apply_if_rate_limited(
            response,
            upstream="osu! API v1",
            endpoint=endpoint,
        )
        if response.status_code in (404, 451):
            osu_api_v1_backoff.record_success(
                upstream="osu! API v1",
                endpoint=endpoint,
            )
            return None
        response.raise_for_status()
        osu_api_response_data = response.json()
        if osu_api_response_data == []:
            osu_api_v1_backoff.record_success(
                upstream="osu! API v1",
                endpoint=endpoint,
            )
            return None
        assert osu_api_response_data is not None
        osu_api_v1_backoff.record_success(upstream="osu! API v1", endpoint=endpoint)
        return Beatmap(**osu_api_response_data[0])
    except OsuApiBackoffError:
        raise
    except Exception:
        osu_api_v1_backoff.record_failure(upstream="osu! API v1", endpoint=endpoint)
        logging.exception(
            "Failed to fetch beatmap from osu! API v1",
            extra={
                "beatmap_id": beatmap_id,
                "osu_api_response_data": osu_api_response_data,
            },
        )
        raise


async def fetch_beatmap_osu_file_data(beatmap_id: int) -> bytes | None:
    osu_api_v1_backoff.raise_if_unavailable(upstream="osu! API v1")

    endpoint = "osu_file"
    try:
        response = await osu_api_v1_http_client.get(f"osu/{beatmap_id}")
        logging.debug(
            "Made request to the v1 osu! api",
            extra={
                "endpoint": "osu_file",
                "authorized": False,
            },
        )
        osu_api_v1_backoff.apply_if_rate_limited(
            response,
            upstream="osu! API v1",
            endpoint=endpoint,
        )
        if response.status_code in (404, 451):
            osu_api_v1_backoff.record_success(
                upstream="osu! API v1",
                endpoint=endpoint,
            )
            return None
        response.raise_for_status()
        osu_api_v1_backoff.record_success(upstream="osu! API v1", endpoint=endpoint)
        return response.read()
    except OsuApiBackoffError:
        raise
    except Exception:
        osu_api_v1_backoff.record_failure(upstream="osu! API v1", endpoint=endpoint)
        logging.exception(
            "Failed to fetch beatmap osu file from osu! API v1",
            extra={"beatmap_id": beatmap_id},
        )
        raise
