from fastapi import APIRouter
from fastapi import Response

from app.adapters.beatmap_mirrors import mirror_aggregate

router = APIRouter()


@router.get("/api/d/{beatmapset_id}")
async def download_beatmapset_osz2(beatmapset_id: int) -> Response:
    beatmap_zip_data = await mirror_aggregate.fetch_beatmap_zip_data(beatmapset_id)
    if beatmap_zip_data is not None:
        return Response(
            beatmap_zip_data,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={beatmapset_id}.osz",
            },
        )
    if isinstance(beatmap_zip_data, mirror_aggregate.TimedOut):
        return Response(status_code=408)

    return Response(status_code=404)
