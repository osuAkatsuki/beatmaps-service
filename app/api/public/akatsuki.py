"""\
Provides an API exposing Akatsuki's beatmaps, which
include internal state such as ranked status updates.
"""

from fastapi import APIRouter
from fastapi import Query
from fastapi import Response

from app.api.responses import JSONResponse
from app.repositories.akatsuki_beatmaps import AkatsukiBeatmapSortBy
from app.repositories.akatsuki_beatmaps import SortOrder
from app.usecases import akatsuki_beatmaps

router = APIRouter(tags=["(Public) Akatsuki Beatmaps"])


@router.get("/public/api/akatsuki/v1/beatmaps")
async def fetch_many_beatmaps(
    only_custom_ranked: bool = False,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    sort_by: AkatsukiBeatmapSortBy = AkatsukiBeatmapSortBy.LATEST_UPDATE,
    sort_order: SortOrder = SortOrder.DESC,
) -> Response:
    beatmaps = await akatsuki_beatmaps.fetch_many(
        only_custom_ranked=only_custom_ranked,
        offset=(page - 1) * limit,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return JSONResponse(
        content=[beatmap.model_dump() for beatmap in beatmaps],
    )
