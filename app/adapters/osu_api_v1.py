import logging
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

# [{
#     "approved"             : "1",                   // 4 = loved, 3 = qualified, 2 = approved, 1 = ranked, 0 = pending, -1 = WIP, -2 = graveyard
#     "submit_date"          : "2013-05-15 11:32:26", // date submitted, in UTC
#     "approved_date"        : "2013-07-06 08:54:46", // date ranked, in UTC
#     "last_update"          : "2013-07-06 08:51:22", // last update date, in UTC. May be after approved_date if map was unranked and reranked.
#     "artist"               : "Luxion",
#     "beatmap_id"           : "252002",              // beatmap_id is per difficulty
#     "beatmapset_id"        : "93398",               // beatmapset_id groups difficulties into a set
#     "bpm"                  : "196",
#     "creator"              : "RikiH_",
#     "creator_id"           : "686209",
#     "difficultyrating"     : "5.744717597961426",   // The number of stars the map would have in-game and on the website
#     "diff_aim"             : "2.7706098556518555",
#     "diff_speed"           : "2.9062750339508057",
#     "diff_size"            : "4",                   // Circle size value (CS)
#     "diff_overall"         : "8",                   // Overall difficulty (OD)
#     "diff_approach"        : "9",                   // Approach Rate (AR)
#     "diff_drain"           : "7",                   // Health drain (HP)
#     "hit_length"           : "114",                 // seconds from first note to last note not including breaks
#     "source"               : "BMS",
#     "genre_id"             : "2",                   // 0 = any, 1 = unspecified, 2 = video game, 3 = anime, 4 = rock, 5 = pop, 6 = other, 7 = novelty, 9 = hip hop, 10 = electronic, 11 = metal, 12 = classical, 13 = folk, 14 = jazz (note that there's no 8)
#     "language_id"          : "5",                   // 0 = any, 1 = unspecified, 2 = english, 3 = japanese, 4 = chinese, 5 = instrumental, 6 = korean, 7 = french, 8 = german, 9 = swedish, 10 = spanish, 11 = italian, 12 = russian, 13 = polish, 14 = other
#     "title"                : "High-Priestess",      // song name
#     "total_length"         : "146",                 // seconds from first note to last note including breaks
#     "version"              : "Overkill",            // difficulty name
#     "file_md5"             : "c8f08438204abfcdd1a748ebfae67421",
#                                                     // md5 hash of the beatmap
#     "mode"                 : "0",                   // game mode,
#     "tags"                 : "kloyd flower roxas",  // Beatmap tags separated by spaces.
#     "favourite_count"      : "140",                 // Number of times the beatmap was favourited. (Americans: notice the ou!)
#     "rating"               : "9.44779",
#     "playcount"            : "94637",               // Number of times the beatmap was played
#     "passcount"            : "10599",               // Number of times the beatmap was passed, completed (the user didn't fail or retry)
#     "count_normal"         : "388",
#     "count_slider"         : "222",
#     "count_spinner"        : "3",
#     "max_combo"            : "899",                 // The maximum combo a user can reach playing this beatmap.
#     "storyboard"           : "0",                   // If this beatmap has a storyboard
#     "video"                : "0",                   // If this beatmap has a video
#     "download_unavailable" : "0",                   // If the download for this beatmap is unavailable (old map, etc.)
#     "audio_unavailable"    : "0"                    // If the audio for this beatmap is unavailable (DMCA takedown, etc.)
# }, { ... }, ...]


class Beatmap(BaseModel):
    approved: int
    submit_date: datetime
    approved_date: datetime
    last_update: datetime
    artist: str
    beatmap_id: int
    beatmapset_id: int
    bpm: int
    creator: str
    creator_id: int
    difficultyrating: float
    diff_aim: float
    diff_speed: float
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
    max_combo: int
    storyboard: int
    video: int
    download_unavailable: int
    audio_unavailable: int


async def get_beatmap(beatmap_id: int) -> Beatmap | None:
    osu_api_response_data: dict[str, Any] | None = None
    try:
        response = await osu_api_v1_http_client.get(
            "get_beatmaps",
            params={
                "k": settings.OSU_API_V1_API_KEY,
                "b": beatmap_id,
            },
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        osu_api_response_data = response.json()
        assert osu_api_response_data is not None
        return Beatmap(**osu_api_response_data)
    except Exception:
        logging.exception(
            "Failed to fetch beatmap from osu! API v1",
            extra={"osu_api_response_data": osu_api_response_data},
        )
        raise
