"""\
Provides an API exposing Akatsuki's beatmaps, which
include internal state such as ranked status updates.
"""

import logging
import time

from fastapi import APIRouter
from fastapi import Header
from fastapi import Response

from app.adapters import osu_api_v1
from app.api.responses import JSONResponse
from app.common_models import RankedStatus
from app.repositories import beatmaps
from app.repositories.beatmaps import AkatsukiBeatmap

router = APIRouter(tags=["Akatsuki Beatmaps"])

IGNORED_BEATMAP_CHARS = dict.fromkeys(map(ord, r':\/*<>?"|'), None)
FROZEN_STATUSES = (RankedStatus.RANKED, RankedStatus.APPROVED, RankedStatus.LOVED)


def parse_akatsuki_beatmaps_from_osu_api_v2(
    osu_api_beatmaps: list[osu_api_v1.Beatmap],
) -> list[AkatsukiBeatmap]:
    # TODO: make sure we are maintaining rules from score-service

    maps: list[AkatsukiBeatmap] = []

    for osu_api_beatmap in osu_api_beatmaps:
        filename = (
            ("{artist} - {title} ({creator}) [{version}].osu")
            .format(
                artist=osu_api_beatmap.artist,
                title=osu_api_beatmap.title,
                creator=osu_api_beatmap.creator,
                version=osu_api_beatmap.version,
            )
            .translate(IGNORED_BEATMAP_CHARS)
        )

        song_name = (
            ("{artist} - {title} [{version}]")
            .format(
                artist=osu_api_beatmap.artist,
                title=osu_api_beatmap.title,
                version=osu_api_beatmap.version,
            )
            .translate(IGNORED_BEATMAP_CHARS)
        )

        bancho_ranked_status = RankedStatus.from_osu_api(osu_api_beatmap.approved)
        frozen = bancho_ranked_status in FROZEN_STATUSES

        od = float(osu_api_beatmap.diff_overall)
        ar = float(osu_api_beatmap.diff_approach)

        maps.append(
            AkatsukiBeatmap(
                beatmap_md5=osu_api_beatmap.file_md5,
                beatmap_id=osu_api_beatmap.beatmap_id,
                beatmapset_id=osu_api_beatmap.beatmapset_id,
                song_name=song_name,
                ranked=bancho_ranked_status,
                playcount=0,
                passcount=0,
                mode=osu_api_beatmap.mode,
                od=od,
                ar=ar,
                hit_length=osu_api_beatmap.hit_length,
                latest_update=int(time.time()),
                max_combo=osu_api_beatmap.max_combo or 0,
                bpm=(
                    round(osu_api_beatmap.bpm) if osu_api_beatmap.bpm is not None else 0
                ),
                file_name=filename,
                ranked_status_freezed=frozen,
                rankedby=None,
                rating=10.0,
                bancho_ranked_status=bancho_ranked_status,
                count_circles=osu_api_beatmap.count_normal,
                count_sliders=osu_api_beatmap.count_slider,
                count_spinners=osu_api_beatmap.count_spinner,
                bancho_creator_id=osu_api_beatmap.creator_id,
                bancho_creator_name=osu_api_beatmap.creator,
            ),
        )

    return maps


@router.get("/api/akatsuki/v1/beatmaps/{beatmap_id}")
async def get_beatmap(
    beatmap_id: int,
    client_ip_address: str | None = Header(None, alias="X-Real-IP"),
    client_user_agent: str | None = Header(None, alias="User-Agent"),
) -> Response:
    beatmap = await beatmaps.fetch_one_by_id(beatmap_id)
    if beatmap is None:
        osu_api_v1_beatmaps = await osu_api_v1.get_beatmap(beatmap_id)
        if osu_api_v1_beatmaps is None:
            return Response(status_code=404)

        new_beatmaps = parse_akatsuki_beatmaps_from_osu_api_v2(osu_api_v1_beatmaps)
        for new_beatmap in new_beatmaps:
            await beatmaps.create(new_beatmap)

        for new_beatmap in new_beatmaps:
            if beatmap_id == new_beatmap.beatmap_id:
                beatmap = new_beatmap
                break
        else:
            return Response(status_code=404)

    logging.info(
        "Serving Akatsuki beatmap",
        extra={
            "beatmap": beatmap.model_dump_json(),
            "client_ip_address": client_ip_address,
            "client_user_agent": client_user_agent,
        },
    )

    return JSONResponse(content=beatmap.model_dump())
