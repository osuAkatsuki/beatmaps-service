import logging
from datetime import datetime
from enum import StrEnum
from typing import Any

import httpx
from pydantic import BaseModel
from pydantic import Field

from app import oauth
from app import settings

OSU_API_V2_TOKEN_ENDPOINT = "https://osu.ppy.sh/oauth/token"


async def log_osu_api_request(request: httpx.Request) -> None:
    if request.url == OSU_API_V2_TOKEN_ENDPOINT:
        return None

    # TODO: migrate this to use statsd
    logging.info(
        "Making authorized request to osu! api",
        extra={"request_url": request.url},
    )
    return None


osu_api_v2_http_client = httpx.AsyncClient(
    base_url="https://osu.ppy.sh/api/v2/",
    auth=oauth.AsyncOAuth(
        client_id=settings.OSU_API_V2_CLIENT_ID,
        client_secret=settings.OSU_API_V2_CLIENT_SECRET,
        token_endpoint=OSU_API_V2_TOKEN_ENDPOINT,
    ),
    event_hooks={"request": [log_osu_api_request]},
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
    max_combo: int | None = None
    bpm: float


class BeatmapExtended(Beatmap):
    accuracy: float
    ar: float
    beatmapset_id: int
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


async def get_beatmap(beatmap_id: int) -> BeatmapExtended | None:
    response = await osu_api_v2_http_client.get(f"beatmaps/{beatmap_id}")
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return BeatmapExtended(**response.json())


class Covers(BaseModel):
    cover: str
    cover2x: str = Field(alias="cover@2x")
    card: str
    card2x: str = Field(alias="card@2x")
    list: str
    list2x: str = Field(alias="list@2x")
    slimcover: str
    slimcover2x: str = Field(alias="slimcover@2x")


class RequiredMeta(BaseModel):
    main_ruleset: int
    non_main_ruleset: int


class NominationsSummary(BaseModel):
    current: int
    eligible_main_rulesets: list[Ruleset] | None = None
    required_meta: RequiredMeta


class Availability(BaseModel):
    download_disabled: bool
    more_information: str | None


class Genre(BaseModel):
    id: int
    name: str


class Description(BaseModel):
    description: str  # (html string)


class Language(BaseModel):
    id: int
    name: str


class Beatmapset(BaseModel):
    artist: str
    artist_unicode: str | None
    covers: Covers
    creator: str
    favourite_count: int
    hype: Any | None  # TODO
    id: int
    nsfw: bool
    offset: int
    play_count: int
    preview_url: str
    source: str
    spotlight: bool
    status: str  # TODO enum
    title: str
    title_unicode: str | None
    user_id: int
    video: bool

    bpm: float | None
    can_be_hyped: bool
    deleted_at: datetime | None
    discussion_enabled: bool
    discussion_locked: bool
    is_scoreable: bool
    last_updated: datetime
    legacy_thread_url: str
    nominations_summary: NominationsSummary
    ranked: int  # TODO: enum
    ranked_date: datetime | None
    storyboard: bool
    submitted_date: datetime
    tags: str

    availability: Availability

    beatmaps: list[BeatmapExtended] | None
    converts: list[BeatmapExtended]
    current_nominations: list[str] | None
    current_user_attributes: Any | None = None  # TODO
    description: Description
    discussions: Any = None  # TODO
    events: Any | None = None  # TODO
    genre: Genre | None = None
    has_favourited: Any = None  # TODO
    language: Language | None = None  # TODO
    pack_tags: list[str] | None
    ratings: Any  # TODO
    recent_favourites: Any  # TODO
    related_users: Any  # TODO
    user: Any  # TODO
    track_id: int | None


async def get_beatmapset(beatmapset_id: int) -> Beatmapset | None:
    response = await osu_api_v2_http_client.get(f"beatmapsets/{beatmapset_id}")
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return Beatmapset(**response.json())
