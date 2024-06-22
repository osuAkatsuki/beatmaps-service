from fastapi import APIRouter
from fastapi import Response

from app.adapters.beatmap_mirrors import mirror_aggregate

router = APIRouter()


@router.get("/api/d/{beatmap_id}")
async def download_beatmapset_osz2(beatmapset_id: int):
    beatmap_zip_data = await mirror_aggregate.fetch_beatmap_zip_data(beatmapset_id)
    if beatmap_zip_data is not None:
        return Response(
            beatmap_zip_data,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={beatmapset_id}.osz",
            },
        )

    return None
