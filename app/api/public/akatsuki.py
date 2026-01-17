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


@router.get("/api/akatsuki/v1/beatmaps/custom-ranked-beatmaps")
async def fetch_all_custom_ranked_beatmaps() -> Response:
    beatmaps = await akatsuki_beatmaps.fetch_all_custom_ranked_beatmaps()
    return JSONResponse(
        content=[AkatsukiBeatmap.model_dump() for AkatsukiBeatmap in beatmaps],
    )
