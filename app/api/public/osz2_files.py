from fastapi import APIRouter
from fastapi import Response

from app.adapters import osu_mirrors

router = APIRouter(tags=["osz2 Files"])


@router.get("/api/d/{beatmapset_id}")
@router.get("/public/api/d/{beatmapset_id}")
async def download_beatmapset_osz2(beatmapset_id: int) -> Response:
    beatmap_zip_data = await osu_mirrors.fetch_beatmap_zip_data(beatmapset_id)
    if beatmap_zip_data is not None:
        return Response(
            beatmap_zip_data,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={beatmapset_id}.osz",
            },
        )

    return Response(status_code=404)
