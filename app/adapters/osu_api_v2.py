from datetime import datetime
from enum import StrEnum

import httpx
from pydantic import BaseModel

from app import oauth
from app import settings

http_client = httpx.AsyncClient(
    base_url="https://osu.ppy.sh/api/v2/",
    auth=oauth.AsyncOAuth(
        client_id=settings.OSU_API_V2_CLIENT_ID,
        client_secret=settings.OSU_API_V2_CLIENT_SECRET,
        token_endpoint="https://osu.ppy.sh/oauth/token",
    ),
    timeout=5.0,
)


class Ruleset(StrEnum):
    OSU = "osu"
    TAIKO = "taiko"
    FRUITS = "fruits"
    MANIA = "mania"


class Failtimes(BaseModel):
    exit: list[int]  # TODO: nullable? osu api says yes
    fail: list[int]  # TODO: nullable? osu api says yes


class Beatmap(BaseModel):
    beatmapset_id: int
    difficulty_rating: float
    id: int
    mode: Ruleset
    status: str  # ranked status (TODO enum?)
    total_length: int
    user_id: int
    version: str

    # TODO: enable this, if desired
    # - Beatmapset for Beatmap objects
    # - BeatmapsetExtended for BeatmapExtended objects
    # - None if there is no associated set (e.g. deleted)
    # beatmapset: Beatmapset | BeatmapsetExtended | None

    checksum: str | None
    failtimes: Failtimes
    max_combo: int


class BeatmapExtended(Beatmap):
    accuracy: float
    ar: float
    beatmapset_id: int
    bpm: float | None
    convert: bool
    count_circles: int
    count_sliders: int
    count_spinners: int
    cs: float
    deleted_at: datetime | None
    drain: float
    hit_length: int
    is_scoreable: bool
    last_updated: datetime
    mode_int: int
    passcount: int
    playcount: int
    ranked: int  # TODO: enum?
    url: str


async def get_beatmap(beatmap_id: int) -> BeatmapExtended:
    response = await http_client.get(f"beatmaps/{beatmap_id}")
    response.raise_for_status()
    return BeatmapExtended(**response.json())
