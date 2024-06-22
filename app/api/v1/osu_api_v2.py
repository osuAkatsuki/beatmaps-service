"""\
Provides an API aligned with the osu! API Specification.

API Spec: https://osu.ppy.sh/docs/index.html

Note: this module only mirrors certain beatmap related APIs.
"""

from fastapi import APIRouter
from fastapi import Response

from app.adapters.osu_api_v2 import api
from app.api.responses import JSONResponse

router = APIRouter()


@router.get("/api/v2/beatmapsets/{beatmapset_id}")
async def get_beatmapset(beatmapset_id: int):
    osu_api_beatmapset = await api.get_beatmapset(beatmapset_id)
    if osu_api_beatmapset is None:
        return Response(status_code=404)

    return JSONResponse(content=osu_api_beatmapset.model_dump())


@router.get("/api/v2/beatmaps/{beatmap_id}")
async def get_beatmap(beatmap_id: int):
    osu_api_beatmap = await api.get_beatmap(beatmap_id)
    if osu_api_beatmap is None:
        return Response(status_code=404)

    return JSONResponse(content=osu_api_beatmap.model_dump())
