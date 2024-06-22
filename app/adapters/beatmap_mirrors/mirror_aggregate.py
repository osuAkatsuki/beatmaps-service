import asyncio
import random
from collections.abc import Awaitable
from collections.abc import Callable
from typing import ParamSpec
from typing import TypeVar

from app.adapters.beatmap_mirrors import BeatmapMirror
from app.adapters.beatmap_mirrors.gatari import GatariMirror
from app.adapters.beatmap_mirrors.mino import MinoMirror
from app.adapters.beatmap_mirrors.nerinyan import NerinyanMirror
from app.adapters.beatmap_mirrors.osu_direct import OsuDirectMirror
from app.adapters.beatmap_mirrors.ripple import RippleMirror

BEATMAP_MIRRORS: list[BeatmapMirror] = [
    GatariMirror(),
    MinoMirror(),
    NerinyanMirror(),
    OsuDirectMirror(),
    # Disabled as ripple only supports ranked maps
    # RippleMirror(),
]


P = ParamSpec("P")
R = TypeVar("R")


async def run_with_semaphore(
    semaphore: asyncio.Semaphore,
    coro: Callable[P, Awaitable[R]],
    *args: P.args,
    **kwargs: P.kwargs,
) -> R:
    async with semaphore:
        return await coro(*args, **kwargs)


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

    # TODO: prioritization based on reliability, speed, etc.
    random.shuffle(BEATMAP_MIRRORS)

    coroutines = [
        asyncio.create_task(
            run_with_semaphore(
                semaphore,
                mirror.fetch_beatmap_zip_data,
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

    return first_result
