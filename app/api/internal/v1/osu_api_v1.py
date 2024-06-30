from fastapi import APIRouter
from fastapi import Response

from app.usecases import osu_files

router = APIRouter(tags=["osu Files"])


@router.get("/api/osu-api/v1/osu-files/{beatmap_id}")
async def download_beatmap_osu_file(beatmap_id: int) -> Response:
    beatmap_osu_file_data = await osu_files.fetch_beatmap_osu_file_data(beatmap_id)
    if beatmap_osu_file_data is None:
        return Response(status_code=404)

    return Response(
        beatmap_osu_file_data,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={beatmap_id}.osu",
        },
    )
