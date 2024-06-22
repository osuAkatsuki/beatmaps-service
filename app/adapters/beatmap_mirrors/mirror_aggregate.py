import asyncio
import logging
import time

from app.adapters.beatmap_mirrors import BeatmapMirror
from app.adapters.beatmap_mirrors.mino import MinoMirror
from app.adapters.beatmap_mirrors.nerinyan import NerinyanMirror
from app.adapters.beatmap_mirrors.osu_direct import OsuDirectMirror

BEATMAP_MIRRORS: list[BeatmapMirror] = [
    MinoMirror(),
    NerinyanMirror(),
    OsuDirectMirror(),
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

    concurrency_limit = 5
    global_timeout = 15
    semaphore = asyncio.Semaphore(concurrency_limit)

    start_time = time.time()

    coroutines = [
        asyncio.create_task(
            run_with_semaphore(
                semaphore,
                mirror,
                beatmapset_id,
            ),
        )
        for mirror in BEATMAP_MIRRORS
    ]
    try:
        done, pending = await asyncio.wait(
            coroutines,
            return_when=asyncio.FIRST_COMPLETED,
            timeout=global_timeout,
        )
        for task in pending:
            task.cancel()
        first_result = await list(done)[0]
    except TimeoutError:
        return None

    # TODO: log which mirrors finished, and which timed out

    mirror, result = first_result
    if result is None:
        return None

    end_time = time.time()
    ms_elapsed = (end_time - start_time) * 1000

    logging.info(
        "A mirror was first to finish during .osz2 aggregate request",
        extra={
            "mirror_name": mirror.name,
            "beatmapset_id": beatmapset_id,
            "ms_elapsed": ms_elapsed,
        },
    )
    return result
