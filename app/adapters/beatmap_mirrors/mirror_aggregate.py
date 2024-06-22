import logging
import random
from datetime import datetime
from datetime import timedelta

from app.adapters.beatmap_mirrors.nerinyan import NerinyanMirror
from app.adapters.beatmap_mirrors.osu_direct import OsuDirectMirror
from app.repositories import beatmap_mirror_requests
from app.scheduling import DynamicWeightedRoundRobin

# from app.adapters.beatmap_mirrors.gatari import GatariMirror
# from app.adapters.beatmap_mirrors.mino import MinoMirror
# from app.adapters.beatmap_mirrors.ripple import RippleMirror

BEATMAP_SELECTOR = DynamicWeightedRoundRobin(
    mirrors=[
        # GatariMirror(),
        # MinoMirror(),
        NerinyanMirror(),
        OsuDirectMirror(),
        # Disabled as ripple only supports ranked maps
        # RippleMirror(),
    ],
)


class TimedOut: ...


TIMED_OUT = TimedOut()


async def fetch_beatmap_zip_data(beatmapset_id: int) -> bytes | TimedOut | None:
    """\
    Fetch a beatmapset .osz2 file by any means necessary, balancing upon
    multiple underlying beatmap mirrors to ensure the best possible
    availability and performance.
    """
    started_at = datetime.now()

    await BEATMAP_SELECTOR.update_all_mirror_and_selector_weights()

    while True:
        mirror = BEATMAP_SELECTOR.select_mirror()
        try:
            beatmap_zip_data = await mirror.fetch_beatmap_zip_data(beatmapset_id)
        except Exception as exc:
            ended_at = datetime.now()
            await beatmap_mirror_requests.create(
                request=beatmap_mirror_requests.BeatmapMirrorRequest(
                    request_url=f"{mirror.base_url}/d/{beatmapset_id}",
                    api_key_id=None,
                    mirror_name=mirror.name,
                    success=False,
                    started_at=started_at,
                    ended_at=ended_at,
                    response_size=None,
                    response_error=str(exc),
                ),
            )
            await BEATMAP_SELECTOR.update_all_mirror_and_selector_weights()
            logging.warning(
                "Failed to fetch beatmap from mirror",
                exc_info=True,
                extra={"mirror": mirror.name},
            )
            continue
        else:
            break

    ended_at = datetime.now()

    await beatmap_mirror_requests.create(
        request=beatmap_mirror_requests.BeatmapMirrorRequest(
            request_url=f"{mirror.base_url}/d/{beatmapset_id}",
            api_key_id=None,
            mirror_name=mirror.name,
            success=True,
            started_at=started_at,
            ended_at=ended_at,
            response_size=(
                len(beatmap_zip_data) if beatmap_zip_data is not None else None
            ),
            response_error=None,
        ),
    )
    await BEATMAP_SELECTOR.update_all_mirror_and_selector_weights()

    ms_elapsed = (ended_at.timestamp() - started_at.timestamp()) * 1000

    logging.info(
        "A mirror was first to finish during .osz2 aggregate request",
        extra={
            "mirror_name": mirror.name,
            "beatmapset_id": beatmapset_id,
            "ms_elapsed": ms_elapsed,
            "data_size": (
                len(beatmap_zip_data) if beatmap_zip_data is not None else None
            ),
            "bad_data": (
                beatmap_zip_data
                if (
                    beatmap_zip_data is not None
                    and (
                        not beatmap_zip_data.startswith(b"PK\x03\x04")
                        or len(beatmap_zip_data) < 20_000
                    )
                )
                else None
            ),
        },
    )
    return beatmap_zip_data
