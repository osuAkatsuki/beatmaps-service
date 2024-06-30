"""\
Provides an API exposing Akatsuki's beatmaps, which
include internal state such as ranked status updates.
"""

import logging

from fastapi import APIRouter
from fastapi import Header
from fastapi import Response

from app.api.responses import JSONResponse
from app.usecases import akatsuki_beatmaps

router = APIRouter(tags=["Akatsuki Beatmaps"])


@router.get("/api/akatsuki/v1/beatmaps/lookup")
async def get_beatmap(
    beatmap_id: int | None = None,
    beatmap_md5: str | None = None,
    client_ip_address: str | None = Header(None, alias="X-Real-IP"),
    client_user_agent: str | None = Header(None, alias="User-Agent"),
) -> Response:
    if [beatmap_id, beatmap_md5].count(None) != 1:
        return Response(status_code=400)

    if beatmap_id is not None:
        beatmap = await akatsuki_beatmaps.fetch_one_by_id(beatmap_id)
        if beatmap is None:
            return Response(status_code=404)
    elif beatmap_md5 is not None:
        beatmap = await akatsuki_beatmaps.fetch_one_by_md5(beatmap_md5)
        if beatmap is None:
            return Response(status_code=404)
    else:
        raise RuntimeError("unreachable")

    logging.debug(
        "Serving Akatsuki beatmap",
        extra={
            "beatmap": beatmap.model_dump(),
            "client_ip_address": client_ip_address,
            "client_user_agent": client_user_agent,
        },
    )

    return JSONResponse(content=beatmap.model_dump())
