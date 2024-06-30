from fastapi import APIRouter
from fastapi import Response

from app.adapters import osu_api_v1

router = APIRouter(tags=["osu Files"])


@router.get("/api/osu-api/v1/osu-files/{beatmap_id}")
async def download_beatmap_osu_file(beatmap_id: int) -> Response:
    beatmap_osu_file_data = await osu_api_v1.fetch_beatmap_osu_file_data(beatmap_id)
    # TODO: consider at which points in beatmaps-service we should update
    #       the .osu file that is currently saved in wasabi s3 storage.
    if beatmap_osu_file_data is None:
        return Response(status_code=404)

    return Response(
        beatmap_osu_file_data,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={beatmap_id}.osu",
        },
    )
