import hashlib
import logging

from app.adapters import aws_s3
from app.adapters import osu_api_v1
from app.repositories import akatsuki_beatmaps


def hash_content(content: bytes) -> str:
    return hashlib.md5(content).hexdigest()


async def _osu_file_cache_expired(
    *,
    beatmap_id: int,
    beatmap_osu_file_data: bytes,
) -> bool:
    akatsuki_beatmap = await akatsuki_beatmaps.fetch_one_by_id(beatmap_id)
    return (
        akatsuki_beatmap is None
        or hash_content(beatmap_osu_file_data) != akatsuki_beatmap.beatmap_md5
    )


async def fetch_beatmap_osu_file_data(beatmap_id: int) -> bytes | None:
    beatmap_osu_file_data = await aws_s3.get_object_data(f"/beatmaps/{beatmap_id}.osu")
    if beatmap_osu_file_data is not None:
        if not await _osu_file_cache_expired(
            beatmap_id=beatmap_id,
            beatmap_osu_file_data=beatmap_osu_file_data,
        ):
            return beatmap_osu_file_data

        logging.info(
            "Updating expired beatmap s3 osu file cache",
            extra={"beatmap_id": beatmap_id},
        )

    beatmap_osu_file_data = await osu_api_v1.fetch_beatmap_osu_file_data(beatmap_id)
    if beatmap_osu_file_data is None:
        return None

    await aws_s3.save_object_data(
        f"/beatmaps/{beatmap_id}.osu",
        beatmap_osu_file_data,
    )
    logging.info(
        "Saved beatmap osu file to s3",
        extra={"beatmap_id": beatmap_id},
    )
    # NOTE: this is a place where .osu files could become desynced
    #       with akatsuki beatmaps in the mysql database, however we've
    #       decided to not worry about this for now, as most use cases
    #       which rely on .osu files will also fetch the beatmap metadata,
    #       forcing an update to occur.

    return beatmap_osu_file_data
