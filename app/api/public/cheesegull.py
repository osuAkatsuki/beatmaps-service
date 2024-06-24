"""\
Provides an API aligned with the Cheesegull API Specification.

API Spec: https://docs.ripple.moe/docs/cheesegull/cheesegull-api
"""

import logging
from datetime import datetime
from enum import IntEnum

from fastapi import APIRouter
from fastapi import Header
from fastapi import Query
from fastapi import Response
from pydantic import BaseModel

from app.adapters.osu_api_v2 import api
from app.adapters.osu_api_v2.models import BeatmapExtended
from app.adapters.osu_api_v2.models import BeatmapsetExtended
from app.adapters.osu_api_v2.models import Category
from app.api.responses import JSONResponse
from app.common_models import GameMode
from app.common_models import RankedStatus

router = APIRouter(tags=["Cheesegull API"])


class CheesegullBeatmap(BaseModel):
    BeatmapID: int
    ParentSetID: int
    DiffName: str
    FileMD5: str
    Mode: int
    BPM: float
    AR: float
    OD: float
    CS: float
    HP: float
    TotalLength: int
    HitLength: int
    Playcount: int
    Passcount: int
    MaxCombo: int
    DifficultyRating: float

    @classmethod
    def from_osu_api_beatmap(
        cls,
        beatmap: BeatmapExtended,
    ) -> "CheesegullBeatmap":
        return cls(
            BeatmapID=beatmap.id,
            ParentSetID=beatmap.beatmapset_id,
            DiffName=beatmap.version,
            FileMD5=beatmap.checksum or "",
            Mode=beatmap.mode_int,
            BPM=beatmap.bpm or 0,
            AR=beatmap.ar,
            OD=beatmap.accuracy,
            CS=beatmap.cs,
            HP=beatmap.drain,
            TotalLength=beatmap.total_length,
            HitLength=beatmap.total_length,
            Playcount=beatmap.playcount,
            Passcount=beatmap.passcount,
            MaxCombo=beatmap.max_combo or 0,
            DifficultyRating=beatmap.difficulty_rating,
        )


class CheesegullBeatmapset(BaseModel):
    SetID: int
    ChildrenBeatmaps: list[CheesegullBeatmap]
    RankedStatus: int
    ApprovedDate: datetime
    LastUpdate: datetime
    LastChecked: datetime
    Artist: str
    Title: str
    Creator: str
    Source: str
    Tags: str
    HasVideo: bool
    Genre: int | None
    Language: int | None
    Favourites: int

    @classmethod
    def from_osu_api_beatmapset(
        cls,
        osu_api_beatmapset: BeatmapsetExtended,
    ) -> "CheesegullBeatmapset":
        children_beatmaps: list[CheesegullBeatmap] = []
        for osu_api_beatmap in osu_api_beatmapset.beatmaps or []:
            if not isinstance(osu_api_beatmap, BeatmapExtended):
                raise ValueError("beatmapset.beatmaps is not a list of BeatmapExtended")
            cheesegull_beatmap = CheesegullBeatmap.from_osu_api_beatmap(osu_api_beatmap)
            children_beatmaps.append(cheesegull_beatmap)

        return cls(
            SetID=osu_api_beatmapset.id,
            ChildrenBeatmaps=children_beatmaps,
            RankedStatus=osu_api_beatmapset.ranked,
            ApprovedDate=osu_api_beatmapset.ranked_date or datetime.min,
            LastUpdate=(
                osu_api_beatmapset.ranked_date or osu_api_beatmapset.last_updated
            ),
            LastChecked=datetime.now(),  # TODO: Implement this
            Artist=osu_api_beatmapset.artist,
            Title=osu_api_beatmapset.title,
            Creator=osu_api_beatmapset.creator,
            Source=osu_api_beatmapset.source,
            Tags=osu_api_beatmapset.tags,
            HasVideo=osu_api_beatmapset.video,
            Genre=osu_api_beatmapset.genre.id if osu_api_beatmapset.genre else None,
            Language=(
                osu_api_beatmapset.language.id if osu_api_beatmapset.language else None
            ),
            Favourites=osu_api_beatmapset.favourite_count,
        )


@router.get("/api/b/{beatmap_id}")
@router.get("/api/public/b/{beatmap_id}")
async def cheesegull_beatmap(
    beatmap_id: int,
    client_ip_address: str | None = Header(None, alias="X-Real-IP"),
    client_user_agent: str | None = Header(None, alias="User-Agent"),
) -> Response:
    osu_api_beatmap = await api.get_beatmap(beatmap_id)
    if osu_api_beatmap is None:
        return Response(status_code=404)

    cheesegull_beatmap = CheesegullBeatmap.from_osu_api_beatmap(osu_api_beatmap)
    logging.debug(
        "Serving cheesegull beatmap",
        extra={
            "beatmap_id": beatmap_id,
            "client_ip_address": client_ip_address,
            "client_user_agent": client_user_agent,
        },
    )
    return JSONResponse(content=cheesegull_beatmap.model_dump())


@router.get("/api/s/{beatmapset_id}")
@router.get("/api/public/s/{beatmapset_id}")
async def cheesegull_beatmapset(
    beatmapset_id: int,
    client_ip_address: str | None = Header(None, alias="X-Real-IP"),
    client_user_agent: str | None = Header(None, alias="User-Agent"),
) -> Response:
    osu_api_beatmapset = await api.get_beatmapset(beatmapset_id)
    if osu_api_beatmapset is None:
        return Response(status_code=404)

    cheesegull_beatmapset = CheesegullBeatmapset.from_osu_api_beatmapset(
        osu_api_beatmapset,
    )
    logging.debug(
        "Serving cheesegull beatmapset",
        extra={
            "beatmapset_id": beatmapset_id,
            "client_ip_address": client_ip_address,
            "client_user_agent": client_user_agent,
        },
    )
    return JSONResponse(content=cheesegull_beatmapset.model_dump())


class CheesegullRankedStatus(IntEnum):
    # This is a limited subset of the osu! api ranked status
    PENDING = 0
    RANKED = 1
    APPROVED = 2
    QUALIFIED = 3
    LOVED = 4


def get_osu_api_v2_search_ranked_status(
    cheesegull_status: CheesegullRankedStatus,
) -> Category | None:
    ranked_status = RankedStatus.from_osu_api(cheesegull_status)
    search_ranked_status = Category.from_ranked_status(ranked_status)
    return search_ranked_status


@router.get("/api/search")
@router.get("/api/public/search")
async def cheesegull_search(
    query: str = "",
    status: CheesegullRankedStatus | None = None,
    mode: GameMode | None = None,
    offset: int = 0,
    amount: int = Query(50, ge=1, le=100),
    client_ip_address: str | None = Header(None, alias="X-Real-IP"),
    client_user_agent: str | None = Header(None, alias="User-Agent"),
    # TODO: auth, or at least per-ip ratelimit
) -> Response:
    if status is not None:
        ranked_status = get_osu_api_v2_search_ranked_status(status)
        if ranked_status is None:
            return Response(status_code=400)
    else:
        ranked_status = None

    num_fetched = 0
    cheesegull_beatmapsets: list[CheesegullBeatmapset] = []
    page = offset // amount + 1
    while num_fetched < amount:
        osu_api_search_response = await api.search_beatmapsets(
            query=query,
            mode=mode,
            category=ranked_status,
            page=page,
        )
        if not osu_api_search_response.beatmapsets:
            break
        cheesegull_beatmapsets.extend(
            [
                CheesegullBeatmapset.from_osu_api_beatmapset(osu_api_beatmapset)
                for osu_api_beatmapset in osu_api_search_response.beatmapsets
            ],
        )
        page += 1
        num_fetched += len(osu_api_search_response.beatmapsets)

    logging.debug(
        "Serving cheesegull search",
        extra={
            "query": query,
            "page": page,
            "results_count": len(cheesegull_beatmapsets),
            "client_ip_address": client_ip_address,
            "client_user_agent": client_user_agent,
        },
    )
    return JSONResponse(
        content=[beatmapset.model_dump() for beatmapset in cheesegull_beatmapsets],
    )
