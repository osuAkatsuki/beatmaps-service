import logging

from app.adapters import aws_s3
from app.adapters import osu_api_v1


async def fetch_beatmap_osu_file_data(beatmap_id: int) -> bytes | None:
    beatmap_osu_file_data = await aws_s3.get_object_data(f"/beatmaps/{beatmap_id}.osu")
    if beatmap_osu_file_data is None:
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
    else:
        # TODO: consider cache expiry
        ...

    return beatmap_osu_file_data
