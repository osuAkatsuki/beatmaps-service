"""\
Provides an API aligned with the Cheesegull API Specification.

API Spec: https://docs.ripple.moe/docs/cheesegull/cheesegull-api
"""

from fastapi import APIRouter
from fastapi import Header
from fastapi import Query
from fastapi import Response

from app.api.responses import JSONResponse
from app.common_models import CheesegullRankedStatus
from app.common_models import GameMode
from app.usecases import cheesegull_beatmaps

router = APIRouter(tags=["(Public) Cheesegull API"])


@router.get("/public/api/b/{beatmap_id}")
async def cheesegull_beatmap(
    beatmap_id: int,
    client_ip_address: str | None = Header(None, alias="X-Real-IP"),
    client_user_agent: str | None = Header(None, alias="User-Agent"),
) -> Response:
    response = await cheesegull_beatmaps.fetch_one_cheesegull_beatmap(
        beatmap_id,
        client_ip_address=client_ip_address,
        client_user_agent=client_user_agent,
    )
    if response is None:
        return Response(status_code=404)

    return JSONResponse(content=response.model_dump())


@router.get("/public/api/s/{beatmapset_id}")
async def cheesegull_beatmapset(
    beatmapset_id: int,
    client_ip_address: str | None = Header(None, alias="X-Real-IP"),
    client_user_agent: str | None = Header(None, alias="User-Agent"),
) -> Response:
    response = await cheesegull_beatmaps.fetch_one_cheesegull_beatmapset(
        beatmapset_id,
        client_ip_address=client_ip_address,
        client_user_agent=client_user_agent,
    )
    if response is None:
        return Response(status_code=404)

    return JSONResponse(content=response.model_dump())


@router.get("/public/api/search")
async def cheesegull_search(
    query: str = "",
    status: CheesegullRankedStatus | None = None,
    mode: GameMode | None = None,
    offset: int = 0,
    amount: int = Query(50, ge=1, le=100),
    client_ip_address: str | None = Header(None, alias="X-Real-IP"),
    client_user_agent: str | None = Header(None, alias="User-Agent"),
    # TODO: auth, or at least per-ip ratelimit
) -> Response:
    response = await cheesegull_beatmaps.cheesegull_search(
        query,
        status,
        mode,
        offset,
        amount,
        client_ip_address=client_ip_address,
        client_user_agent=client_user_agent,
    )
    if response is None:
        return Response(status_code=404)

    return JSONResponse(content=[beatmap.model_dump() for beatmap in response])
