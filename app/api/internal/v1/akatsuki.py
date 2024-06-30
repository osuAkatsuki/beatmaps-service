"""\
Provides an API exposing Akatsuki's beatmaps, which
include internal state such as ranked status updates.
"""

import logging

from fastapi import APIRouter
from fastapi import Header
from fastapi import Response

from app.adapters.osu_api_v2 import api as osu_api_v2
from app.adapters.osu_api_v2.models import BeatmapExtended
from app.api.responses import JSONResponse
from app.repositories import beatmaps
from app.repositories.beatmaps import AkatsukiBeatmap

router = APIRouter(tags=["Akatsuki Beatmaps"])


def parse_akatsuki_beatmap_from_osu_api_v2(
    osu_api_beatmap: BeatmapExtended,
) -> AkatsukiBeatmap: ...  # TODO


@router.get("/api/akatsuki/v1/beatmaps/{beatmap_id}")
async def get_beatmap(
    beatmap_id: int,
    client_ip_address: str | None = Header(None, alias="X-Real-IP"),
    client_user_agent: str | None = Header(None, alias="User-Agent"),
) -> Response:
    """Get a beatmap by its ID."""
    beatmap = await beatmaps.fetch_one_by_id(beatmap_id)
    if beatmap is None:
        osu_api_v2_beatmap = await osu_api_v2.get_beatmap(beatmap_id)
        if osu_api_v2_beatmap is None:
            return Response(status_code=404)

        beatmap = parse_akatsuki_beatmap_from_osu_api_v2(osu_api_v2_beatmap)
        # TODO: make sure we are maintaining rules from score-service
        beatmap = await beatmaps.create(beatmap)

    logging.info(
        "Serving Akatsuki beatmap",
        extra={
            "beatmap": beatmap.model_dump_json(),
            "client_ip_address": client_ip_address,
            "client_user_agent": client_user_agent,
        },
    )

    return JSONResponse(content=beatmap.model_dump())
