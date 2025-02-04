import logging
from datetime import datetime

from app.adapters import osu_mirrors
from app.adapters.osu_api_v2 import api as osu_api_v2
from app.adapters.osu_api_v2.models import BeatmapExtended
from app.adapters.osu_api_v2.models import BeatmapsetExtended
from app.adapters.osu_api_v2.models import Category
from app.api.responses import JSONResponse
from app.common_models import CheesegullBeatmap
from app.common_models import CheesegullBeatmapset
from app.common_models import CheesegullRankedStatus
from app.common_models import GameMode
from app.common_models import RankedStatus


def cheesegull_beatmap_from_osu_api_beatmap(
    beatmap: BeatmapExtended,
) -> "CheesegullBeatmap":
    return CheesegullBeatmap(
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


def cheesegull_beatmapset_from_osu_api_beatmapset(
    osu_api_beatmapset: BeatmapsetExtended,
) -> "CheesegullBeatmapset":
    children_beatmaps: list[CheesegullBeatmap] = []
    for osu_api_beatmap in osu_api_beatmapset.beatmaps or []:
        if not isinstance(osu_api_beatmap, BeatmapExtended):
            raise ValueError("beatmapset.beatmaps is not a list of BeatmapExtended")
        cheesegull_beatmap = cheesegull_beatmap_from_osu_api_beatmap(osu_api_beatmap)
        children_beatmaps.append(cheesegull_beatmap)

    return CheesegullBeatmapset(
        SetID=osu_api_beatmapset.id,
        ChildrenBeatmaps=children_beatmaps,
        RankedStatus=osu_api_beatmapset.ranked,
        ApprovedDate=osu_api_beatmapset.ranked_date or datetime.min,
        LastUpdate=(osu_api_beatmapset.ranked_date or osu_api_beatmapset.last_updated),
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


def get_osu_api_v2_search_ranked_status(
    cheesegull_status: CheesegullRankedStatus,
) -> Category | None:
    ranked_status = RankedStatus.from_osu_api(cheesegull_status)
    search_ranked_status = Category.from_ranked_status(ranked_status)
    return search_ranked_status


async def fetch_one_cheesegull_beatmap(
    beatmap_id: int,
    *,
    client_ip_address: str | None,
    client_user_agent: str | None,
) -> CheesegullBeatmap | None:
    try:
        try:
            osu_api_beatmap = await osu_api_v2.get_beatmap(beatmap_id)
            if osu_api_beatmap is None:
                return None

            cheesegull_beatmap: CheesegullBeatmap | None = (
                cheesegull_beatmap_from_osu_api_beatmap(
                    osu_api_beatmap,
                )
            )
        except Exception:
            # Fallback to mirror
            cheesegull_beatmap = await osu_mirrors.fetch_one_cheesegull_beatmap(
                beatmap_id,
            )
            if cheesegull_beatmap is None:
                return None

        logging.debug(
            "Serving cheesegull beatmap",
            extra={
                "beatmap_id": beatmap_id,
                "client_ip_address": client_ip_address,
                "client_user_agent": client_user_agent,
            },
        )
        return cheesegull_beatmap
    except Exception:
        logging.exception(
            "Failed to fetch cheesegull beatmap",
            extra={
                "beatmap_id": beatmap_id,
                "client_ip_address": client_ip_address,
                "client_user_agent": client_user_agent,
            },
        )
        return None


async def fetch_one_cheesegull_beatmapset(
    beatmapset_id: int,
    *,
    client_ip_address: str | None,
    client_user_agent: str | None,
) -> CheesegullBeatmapset | None:
    try:
        try:
            osu_api_beatmapset = await osu_api_v2.get_beatmapset(beatmapset_id)
            if osu_api_beatmapset is None:
                return None
            cheesegull_beatmapset: CheesegullBeatmapset | None = (
                cheesegull_beatmapset_from_osu_api_beatmapset(
                    osu_api_beatmapset,
                )
            )
        except Exception:
            # Fallback to mirror
            cheesegull_beatmapset = await osu_mirrors.fetch_one_cheesegull_beatmapset(
                beatmapset_id,
            )
            if cheesegull_beatmapset is None:
                return None

        logging.debug(
            "Serving cheesegull beatmapset",
            extra={
                "beatmapset_id": beatmapset_id,
                "client_ip_address": client_ip_address,
                "client_user_agent": client_user_agent,
            },
        )
        return cheesegull_beatmapset
    except Exception:
        logging.exception(
            "Failed to fetch cheesegull beatmapset",
            extra={
                "beatmapset_id": beatmapset_id,
                "client_ip_address": client_ip_address,
                "client_user_agent": client_user_agent,
            },
        )
        return None


async def cheesegull_search(
    query: str,
    status: CheesegullRankedStatus | None,
    mode: GameMode | None,
    offset: int,
    amount: int,
    client_ip_address: str | None,
    client_user_agent: str | None,
) -> list[CheesegullBeatmapset] | None:
    try:
        if status is not None:
            ranked_status = get_osu_api_v2_search_ranked_status(status)
            if ranked_status is None:
                logging.warning(
                    "Invalid cheesegull search status",
                    extra={
                        "search_status": status,
                        "client_ip_address": client_ip_address,
                        "client_user_agent": client_user_agent,
                    },
                )
                return None
        else:
            ranked_status = None

        num_fetched = 0
        cheesegull_beatmapsets: list[CheesegullBeatmapset] = []
        page = offset // amount + 1
        while num_fetched < amount:
            osu_api_search_response = await osu_api_v2.search_beatmapsets(
                query=query,
                mode=mode,
                category=ranked_status,
                page=page,
            )
            if not osu_api_search_response.beatmapsets:
                break
            cheesegull_beatmapsets.extend(
                [
                    cheesegull_beatmapset_from_osu_api_beatmapset(osu_api_beatmapset)
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
        return cheesegull_beatmapsets
    except Exception:
        logging.exception(
            "Failed to fetch cheesegull search",
            extra={
                "query": query,
                "client_ip_address": client_ip_address,
                "client_user_agent": client_user_agent,
            },
        )
        return None
