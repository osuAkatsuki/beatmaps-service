import asyncio
import logging
import random
import time

from pydantic import BaseModel

from app.adapters.beatmap_mirrors import BeatmapMirror

from app.adapters.beatmap_mirrors.nerinyan import NerinyanMirror
from app.adapters.beatmap_mirrors.osu_direct import OsuDirectMirror

# from app.adapters.beatmap_mirrors.gatari import GatariMirror
# from app.adapters.beatmap_mirrors.mino import MinoMirror
# from app.adapters.beatmap_mirrors.ripple import RippleMirror

BEATMAP_MIRRORS: list[BeatmapMirror] = [
    # GatariMirror(),
    # MinoMirror(),
    NerinyanMirror(),
    OsuDirectMirror(),
    # Disabled as ripple only supports ranked maps
    # RippleMirror(),
]


async def run_with_semaphore(
    semaphore: asyncio.Semaphore,
    mirror: BeatmapMirror,
    beatmapset_id: int,
) -> tuple[BeatmapMirror, bytes | None]:
    async with semaphore:
        return (mirror, await mirror.fetch_beatmap_zip_data(beatmapset_id))


class TimedOut: ...


TIMED_OUT = TimedOut()


class BeatmapMirrorRequest(BaseModel):
    request_url: str
    api_key_id: str | None
    mirror_name: str
    success: bool
    started_at: float
    ended_at: float
    response_code: int | None
    response_size: int | None
    response_error: str | None


async def fetch_beatmap_zip_data(beatmapset_id: int) -> bytes | TimedOut | None:
    """\
    Parallelize calls with a timeout across up to 5 mirrors at time,
    to ensure our clients get a response in a reasonable time.
    """

    # TODO: it would be nice to be able to stream the responses,
    #       but that would require a different approach where the
    #       discovery process would be complete once the mirror has
    #       started streaming, rather than after the response has
    #       been read in full.

    start_time = time.time()
    for mirror in BEATMAP_MIRRORS:
        try:
            result = await mirror.fetch_beatmap_zip_data(beatmapset_id)
        except Exception:
            # TODO: log failure to `beatmap_mirror_requests` table
            logging.warning(
                "Failed to fetch beatmap from mirror",
                exc_info=True,
                extra={"mirror": mirror.name},
            )
            continue
        else:
            break
    else:
        return TIMED_OUT

    if result is None:
        return None

    # TODO: log success to `beatmap_mirror_requests` table

    end_time = time.time()

    ms_elapsed = (end_time - start_time) * 1000

    logging.info(
        "A mirror was first to finish during .osz2 aggregate request",
        extra={
            "mirror_name": mirror.name,
            "beatmapset_id": beatmapset_id,
            "ms_elapsed": ms_elapsed,
            "data_size": len(result),
            "bad_data": (
                result
                if not result.startswith(b"PK\x03\x04") or len(result) < 20_000
                else None
            ),
        },
    )
    return result
