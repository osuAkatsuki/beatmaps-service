import logging
from datetime import datetime

from app.adapters.osu_mirrors.backends import AbstractBeatmapMirror
from app.adapters.osu_mirrors.backends.mino import MinoMirror

# from app.adapters.osu_mirrors.backends.mino import MinoCentralMirror
# from app.adapters.osu_mirrors.backends.mino import MinoSingaporeMirror
# from app.adapters.osu_mirrors.backends.mino import MinoUSMirror
from app.adapters.osu_mirrors.backends.nerinyan import NerinyanMirror
from app.adapters.osu_mirrors.backends.osu_direct import OsuDirectMirror
from app.adapters.osu_mirrors.selectors.dynamic_round_robin import (
    DynamicWeightedRoundRobinMirrorSelector,
)
from app.common_models import CheesegullBeatmap
from app.common_models import CheesegullBeatmapset
from app.repositories import beatmap_mirror_requests
from app.repositories.beatmap_mirror_requests import MirrorResource

ZIP_FILE_HEADER = b"PK\x03\x04"

BEATMAP_MIRRORS: list[AbstractBeatmapMirror] = [
    MinoMirror(),
    # MinoCentralMirror(),
    # MinoUSMirror(),
    # MinoSingaporeMirror(),
    NerinyanMirror(),
    OsuDirectMirror(),
    # GatariMirror(),  # Disabled as ratelimit is very low
    # RippleMirror(),  # Disabled as only ranked maps are supported
]
OSZ_FILE_MIRROR_SELECTOR = DynamicWeightedRoundRobinMirrorSelector(
    mirrors=[
        mirror
        for mirror in BEATMAP_MIRRORS
        if MirrorResource.OSZ_FILE in mirror.supported_resources
    ],
    resource=MirrorResource.OSZ_FILE,
)
BACKGROUND_IMAGE_MIRROR_SELECTOR = DynamicWeightedRoundRobinMirrorSelector(
    mirrors=[
        mirror
        for mirror in BEATMAP_MIRRORS
        if MirrorResource.BACKGROUND_IMAGE in mirror.supported_resources
    ],
    resource=MirrorResource.BACKGROUND_IMAGE,
)


def is_valid_zip_file(content: bytes) -> bool:
    return content.startswith(ZIP_FILE_HEADER)


async def fetch_one_cheesegull_beatmap(beatmap_id: int) -> CheesegullBeatmap | None:
    mirror = OsuDirectMirror()  # TODO

    started_at = datetime.now()
    mirror_response = await mirror.fetch_one_cheesegull_beatmap(beatmap_id)
    ended_at = datetime.now()

    await beatmap_mirror_requests.create(
        request_url=mirror_response.request_url or "unavailable",
        api_key_id=None,
        mirror_name=mirror.name,
        success=mirror_response.is_success,
        started_at=started_at,
        ended_at=ended_at,
        response_status_code=mirror_response.status_code,
        response_size=(
            len(mirror_response.data.model_dump_json()) if mirror_response.data else 0
        ),
        response_error=mirror_response.error_message,
        resource=MirrorResource.OSZ_FILE,
    )

    if not mirror_response.is_success:
        logging.warning(
            "Failed to fetch cheesegull beatmap from mirror",
            exc_info=True,
            extra={
                "response": {
                    "url": mirror_response.request_url,
                    "status_code": mirror_response.status_code,
                },
                "mirror_name": mirror.name,
                "mirror_weight": mirror.weight,
                "beatmap_id": beatmap_id,
            },
        )
        return None

    ms_elapsed = (ended_at.timestamp() - started_at.timestamp()) * 1000

    logging.debug(
        "Served cheesegull beatmap from mirror",
        extra={
            "mirror_name": mirror.name,
            "mirror_weight": mirror.weight,
            "beatmap_id": beatmap_id,
            "ms_elapsed": ms_elapsed,
            "data_size": (
                len(mirror_response.data.model_dump_json())
                if mirror_response.data
                else 0
            ),
        },
    )

    return mirror_response.data


async def fetch_one_cheesegull_beatmapset(
    beatmapset_id: int,
) -> CheesegullBeatmapset | None:
    mirror = OsuDirectMirror()  # TODO

    started_at = datetime.now()
    mirror_response = await mirror.fetch_one_cheesegull_beatmapset(beatmapset_id)
    ended_at = datetime.now()

    await beatmap_mirror_requests.create(
        request_url=mirror_response.request_url or "unavailable",
        api_key_id=None,
        mirror_name=mirror.name,
        success=mirror_response.is_success,
        started_at=started_at,
        ended_at=ended_at,
        response_status_code=mirror_response.status_code,
        response_size=(
            len(mirror_response.data.model_dump_json()) if mirror_response.data else 0
        ),
        response_error=mirror_response.error_message,
        resource=MirrorResource.OSZ_FILE,
    )

    if not mirror_response.is_success:
        logging.warning(
            "Failed to fetch cheesegull beatmapset from mirror",
            exc_info=True,
            extra={
                "response": {
                    "url": mirror_response.request_url,
                    "status_code": mirror_response.status_code,
                },
                "mirror_name": mirror.name,
                "mirror_weight": mirror.weight,
                "beatmapset_id": beatmapset_id,
            },
        )
        return None

    ms_elapsed = (ended_at.timestamp() - started_at.timestamp()) * 1000

    logging.debug(
        "Served cheesegull beatmapset from mirror",
        extra={
            "mirror_name": mirror.name,
            "mirror_weight": mirror.weight,
            "beatmapset_id": beatmapset_id,
            "ms_elapsed": ms_elapsed,
            "data_size": (
                len(mirror_response.data.model_dump_json())
                if mirror_response.data
                else 0
            ),
        },
    )

    return mirror_response.data


async def fetch_beatmap_zip_data(beatmapset_id: int) -> bytes | None:
    """\
    Fetch a beatmapset .osz file by any means necessary, balancing upon
    multiple underlying beatmap mirrors to ensure the best possible
    availability and performance.
    """
    prev_mirror: AbstractBeatmapMirror | None = None
    num_attempts = 0

    await OSZ_FILE_MIRROR_SELECTOR.update_all_mirror_and_selector_weights()

    while True:
        mirror = OSZ_FILE_MIRROR_SELECTOR.select_mirror()
        if mirror is prev_mirror:
            # don't allow the same mirror to be run twice, to help
            # prevent loops which cause the mirror to lose all weighting
            # because of an error on a single beatmapset
            continue

        # Only retry up to 2x the number of mirrors
        if num_attempts > OSZ_FILE_MIRROR_SELECTOR.get_num_mirrors() * 2:
            logging.warning(
                "Failed to fetch beatmapset osz from any mirror",
                extra={"beatmapset_id": beatmapset_id},
            )
            return None

        num_attempts += 1

        started_at = datetime.now()
        mirror_response = await mirror.fetch_beatmap_zip_data(beatmapset_id)
        ended_at = datetime.now()

        if mirror_response.is_success:
            if mirror_response.data is not None and not is_valid_zip_file(
                mirror_response.data,
            ):
                mirror_response.is_success = False
                mirror_response.error_message = "Invalid .osz file"

        await beatmap_mirror_requests.create(
            request_url=mirror_response.request_url or "unavailable",
            api_key_id=None,
            mirror_name=mirror.name,
            success=mirror_response.is_success,
            started_at=started_at,
            ended_at=ended_at,
            response_status_code=mirror_response.status_code,
            response_size=len(mirror_response.data) if mirror_response.data else 0,
            response_error=mirror_response.error_message,
            resource=MirrorResource.OSZ_FILE,
        )
        await OSZ_FILE_MIRROR_SELECTOR.update_all_mirror_and_selector_weights()

        if mirror_response.is_success:
            break

        logging.warning(
            "Failed to fetch beatmapset osz from mirror",
            exc_info=True,
            extra={
                "response": {
                    "url": mirror_response.request_url,
                    "status_code": mirror_response.status_code,
                },
                "mirror_name": mirror.name,
                "mirror_weight": mirror.weight,
                "beatmapset_id": beatmapset_id,
            },
        )
        prev_mirror = mirror
        continue

    ms_elapsed = (ended_at.timestamp() - started_at.timestamp()) * 1000

    logging.debug(
        "Served beatmapset osz from mirror",
        extra={
            "mirror_name": mirror.name,
            "mirror_weight": mirror.weight,
            "beatmapset_id": beatmapset_id,
            "ms_elapsed": ms_elapsed,
            "data_size": len(mirror_response.data) if mirror_response.data else 0,
        },
    )
    return mirror_response.data


async def fetch_beatmap_background_image(beatmap_id: int) -> bytes | None:
    """\
    Fetch a beatmap background image by any means necessary, balancing upon
    multiple underlying beatmap mirrors to ensure the best possible
    availability and performance.
    """
    prev_mirror: AbstractBeatmapMirror | None = None
    num_attempts = 0

    await BACKGROUND_IMAGE_MIRROR_SELECTOR.update_all_mirror_and_selector_weights()

    while True:
        mirror = BACKGROUND_IMAGE_MIRROR_SELECTOR.select_mirror()
        if mirror is prev_mirror:
            # don't allow the same mirror to be run twice, to help
            # prevent loops which cause the mirror to lose all weighting
            # because of an error on a single beatmapset
            continue

        # Only retry up to 2x the number of mirrors
        if num_attempts > BACKGROUND_IMAGE_MIRROR_SELECTOR.get_num_mirrors() * 2:
            logging.warning(
                "Failed to fetch beatmap background image from any mirror",
                extra={"beatmap_id": beatmap_id},
            )
            return None

        num_attempts += 1

        started_at = datetime.now()
        mirror_response = await mirror.fetch_beatmap_background_image(beatmap_id)
        ended_at = datetime.now()

        await beatmap_mirror_requests.create(
            request_url=mirror_response.request_url or "unavailable",
            api_key_id=None,
            mirror_name=mirror.name,
            success=mirror_response.is_success,
            started_at=started_at,
            ended_at=ended_at,
            response_status_code=mirror_response.status_code,
            response_size=len(mirror_response.data) if mirror_response.data else 0,
            response_error=mirror_response.error_message,
            resource=MirrorResource.BACKGROUND_IMAGE,
        )
        await BACKGROUND_IMAGE_MIRROR_SELECTOR.update_all_mirror_and_selector_weights()

        if mirror_response.is_success:
            break

        logging.warning(
            "Failed to fetch beatmap background image from mirror",
            exc_info=True,
            extra={
                "response": {
                    "url": mirror_response.request_url,
                    "status_code": mirror_response.status_code,
                },
                "mirror_name": mirror.name,
                "mirror_weight": mirror.weight,
                "beatmap_id": beatmap_id,
            },
        )
        prev_mirror = mirror
        continue

    ms_elapsed = (ended_at.timestamp() - started_at.timestamp()) * 1000

    logging.debug(
        "Served beatmap background image from mirror",
        extra={
            "mirror_name": mirror.name,
            "mirror_weight": mirror.weight,
            "beatmap_id": beatmap_id,
            "ms_elapsed": ms_elapsed,
            "data_size": len(mirror_response.data) if mirror_response.data else 0,
        },
    )
    return mirror_response.data
