"""\
Provides an API exposing Akatsuki's beatmaps, which
include internal state such as ranked status updates.
"""

from fastapi import APIRouter
from fastapi import Query
from fastapi import Response

from app.api.responses import JSONResponse
from app.usecases import akatsuki_beatmaps

router = APIRouter(tags=["(Public) Akatsuki Beatmaps"])


@router.get("/api/akatsuki/v1/beatmaps")
async def fetch_many_beatmaps(
    only_custom_ranked: bool = False,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
) -> Response:
    beatmaps = await akatsuki_beatmaps.fetch_many(
        only_custom_ranked=only_custom_ranked,
        offset=(page - 1) * limit,
        limit=limit,
    )
    return JSONResponse(
        content=[beatmap.model_dump() for beatmap in beatmaps],
    )
