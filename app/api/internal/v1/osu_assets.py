import logging

from fastapi import APIRouter
from fastapi import Header
from fastapi import Response

from app.adapters import osu_mirrors

router = APIRouter(tags=["osu! Media Assets"])


@router.get("/api/osu-assets/backgrounds/{beatmap_id}")
async def get_beatmap_background(
    beatmap_id: int,
    client_ip_address: str | None = Header(None, alias="X-Real-IP"),
    client_user_agent: str | None = Header(None, alias="User-Agent"),
) -> Response:
    background_image_data = await osu_mirrors.fetch_beatmap_background_image(beatmap_id)
    if background_image_data is None:
        return Response(status_code=404)

    logging.info(
        "Serving osu! API v2 background",
        extra={
            "beatmap_id": beatmap_id,
            "client_ip_address": client_ip_address,
            "client_user_agent": client_user_agent,
        },
    )

    return Response(background_image_data, media_type="image/jpeg")
