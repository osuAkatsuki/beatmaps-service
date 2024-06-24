"""\
Provides an API aligned with the osu! API Specification.

API Spec: https://osu.ppy.sh/docs/index.html

The goal here is to provide a straight pipe through to the osu! API.

**This API guarantees up-to-date responses from the osu! API**,
as it does not cache any data.
"""

import logging

from fastapi import APIRouter
from fastapi import Header
from fastapi import Response

from app.adapters.osu_api_v2 import api
from app.api.responses import JSONResponse

router = APIRouter(tags=["osu! API Straight Pipes"])


@router.get("/api/osu-api/v2/beatmapsets/{beatmapset_id}")
async def get_beatmapset(
    beatmapset_id: int,
    client_ip_address: str | None = Header(None, alias="X-Real-IP"),
    client_user_agent: str | None = Header(None, alias="User-Agent"),
) -> Response:
    osu_api_beatmapset = await api.get_beatmapset(beatmapset_id)
    if osu_api_beatmapset is None:
        return Response(status_code=404)

    logging.info(
        "Serving osu! API v2 beatmapset",
        extra={
            "beatmapset_id": beatmapset_id,
            "client_ip_address": client_ip_address,
            "client_user_agent": client_user_agent,
        },
    )

    return JSONResponse(content=osu_api_beatmapset.model_dump())


@router.get("/api/osu-api/v2/beatmaps/{beatmap_id}")
async def get_beatmap(
    beatmap_id: int,
    client_ip_address: str | None = Header(None, alias="X-Real-IP"),
    client_user_agent: str | None = Header(None, alias="User-Agent"),
) -> Response:
    osu_api_beatmap = await api.get_beatmap(beatmap_id)
    if osu_api_beatmap is None:
        return Response(status_code=404)

    logging.info(
        "Serving osu! API v2 beatmap",
        extra={
            "beatmap_id": beatmap_id,
            "client_ip_address": client_ip_address,
            "client_user_agent": client_user_agent,
        },
    )

    return JSONResponse(content=osu_api_beatmap.model_dump())
