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
@router.get("/api/akatsuki/v1/beatmaps/akatsuki_beatmaps_lookup") #changed name from lookup
async def get_beatmap(
    beatmap_id: int | None = None,
    beatmap_md5: str | None = None,
    client_ip_address: str | None = Header(None, alias="X-Real-IP"),
    client_user_agent: str | None = Header(None, alias="User-Agent"),
) -> Response:
    #idk if stuff above with get_beatmap is needed
    beatmaps = await akatsuki_beatmaps.fetch_all_custom_ranked_beatmaps()
    return JSONResponse(content=[AkatsukiBeatmap.model_dump() for AkatsukiBeatmap in beatmaps])