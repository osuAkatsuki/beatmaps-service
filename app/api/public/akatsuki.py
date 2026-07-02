"""\
Provides an API exposing Akatsuki's beatmaps, which
include internal state such as ranked status updates.
"""

from fastapi import APIRouter
from fastapi import Query
from fastapi import Response

from app.api.responses import JSONResponse
from app.common_models import GameMode
from app.common_models import RankedStatus
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
    ranked: list[RankedStatus] | None = Query(None),
    mode: list[GameMode] | None = Query(None),
    bancho_creator_id: int | None = Query(None, ge=0),
    bancho_creator_name: str | None = Query(None, min_length=1),
    rankedby: int | None = Query(None, ge=0),
) -> Response:
    beatmaps = await akatsuki_beatmaps.fetch_many(
        only_custom_ranked=only_custom_ranked,
        offset=(page - 1) * limit,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        ranked=ranked,
        mode=mode,
        bancho_creator_id=bancho_creator_id,
        bancho_creator_name=bancho_creator_name,
        rankedby=rankedby,
    )
    return JSONResponse(
        content=[beatmap.model_dump() for beatmap in beatmaps],
    )
