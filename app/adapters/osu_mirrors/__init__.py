import logging
from datetime import datetime

from app.adapters.osu_mirrors.backends import AbstractBeatmapMirror
from app.adapters.osu_mirrors.backends.mino import MinoMirror
from app.adapters.osu_mirrors.backends.nerinyan import NerinyanMirror
from app.adapters.osu_mirrors.backends.osu_direct import OsuDirectMirror
from app.adapters.osu_mirrors.selectors.dynamic_round_robin import (
    DynamicWeightedRoundRobinMirrorSelector,
)
from app.repositories import beatmap_mirror_requests
from app.repositories.beatmap_mirror_requests import BeatmapMirrorResource

ZIP_FILE_HEADER = b"PK\x03\x04"

BEATMAP_SELECTOR = DynamicWeightedRoundRobinMirrorSelector(
    mirrors=[
        MinoMirror(),
        NerinyanMirror(),
        OsuDirectMirror(),
        # GatariMirror(),  # Disabled as ratelimit is very low
        # RippleMirror(),  # Disabled as only ranked maps are supported
    ],
)


def is_valid_zip_file(content: bytes) -> bool:
    return content.startswith(ZIP_FILE_HEADER)


async def fetch_beatmap_zip_data(beatmapset_id: int) -> bytes | None:
    """\
    Fetch a beatmapset .osz2 file by any means necessary, balancing upon
    multiple underlying beatmap mirrors to ensure the best possible
    availability and performance.
    """
    prev_mirror: AbstractBeatmapMirror | None = None
    num_attempts = 0

    await BEATMAP_SELECTOR.update_all_mirror_and_selector_weights()

    while True:
        mirror = BEATMAP_SELECTOR.select_mirror()
        if mirror is prev_mirror:
            # don't allow the same mirror to be run twice, to help
            # prevent loops which cause the mirror to lose all weighting
            # because of an error on a single beatmapset
            continue

        # Only retry up to 2x the number of mirrors
        if num_attempts > BEATMAP_SELECTOR.get_num_mirrors() * 2:
            logging.warning(
                "Failed to fetch beatmapset osz2 from any mirror",
                extra={"beatmapset_id": beatmapset_id},
            )
            return None

        num_attempts += 1
        started_at = datetime.now()

        beatmap_zip_data: bytes | None = None
        try:
            beatmap_zip_data = await mirror.fetch_beatmap_zip_data(beatmapset_id)
            if beatmap_zip_data is not None and not is_valid_zip_file(beatmap_zip_data):
                raise ValueError("Received bad osz2 data from mirror")
        except Exception as exc:
            ended_at = datetime.now()
            await beatmap_mirror_requests.create(
                request_url=f"{mirror.base_url}/d/{beatmapset_id}",
                api_key_id=None,
                mirror_name=mirror.name,
                success=False,
                started_at=started_at,
                ended_at=ended_at,
                response_size=len(beatmap_zip_data) if beatmap_zip_data else 0,
                response_error=str(exc),
                resource=BeatmapMirrorResource.OSZ2_FILE,
            )
            await BEATMAP_SELECTOR.update_all_mirror_and_selector_weights()
            logging.warning(
                "Failed to fetch beatmapset osz2 from mirror",
                exc_info=True,
                extra={
                    "mirror_name": mirror.name,
                    "mirror_weight": mirror.weight,
                    "beatmapset_id": beatmapset_id,
                },
            )
            prev_mirror = mirror
            continue
        else:
            break

    ended_at = datetime.now()

    await beatmap_mirror_requests.create(
        request_url=f"{mirror.base_url}/d/{beatmapset_id}",
        api_key_id=None,
        mirror_name=mirror.name,
        success=True,
        started_at=started_at,
        ended_at=ended_at,
        response_size=len(beatmap_zip_data) if beatmap_zip_data else 0,
        response_error=None,
        resource=BeatmapMirrorResource.OSZ2_FILE,
    )
    await BEATMAP_SELECTOR.update_all_mirror_and_selector_weights()

    ms_elapsed = (ended_at.timestamp() - started_at.timestamp()) * 1000

    logging.info(
        "Served beatmapset osz2 from mirror",
        extra={
            "mirror_name": mirror.name,
            "mirror_weight": mirror.weight,
            "beatmapset_id": beatmapset_id,
            "ms_elapsed": ms_elapsed,
            "data_size": len(beatmap_zip_data) if beatmap_zip_data is not None else 0,
        },
    )
    return beatmap_zip_data
