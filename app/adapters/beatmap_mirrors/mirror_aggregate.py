import logging

from datetime import datetime
from datetime import timedelta

from app.adapters.beatmap_mirrors import BeatmapMirror

from app.adapters.beatmap_mirrors.nerinyan import NerinyanMirror
from app.adapters.beatmap_mirrors.osu_direct import OsuDirectMirror
from app.repositories import beatmap_mirror_requests

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


class TimedOut: ...


TIMED_OUT = TimedOut()


async def fetch_beatmap_zip_data(beatmapset_id: int) -> bytes | TimedOut | None:
    """\
    Fetch a beatmapset .osz2 file by any means necessary, balancing upon
    multiple underlying beatmap mirrors to ensure the best possible
    availability and performance.
    """
    started_at = datetime.now()

    for beatmap_mirror in BEATMAP_MIRRORS:
        if beatmap_mirror.score_last_updated_at < (
            datetime.now() - timedelta(minutes=5)
        ):
            beatmap_mirror.score = await beatmap_mirror_requests.get_mirror_score(
                beatmap_mirror.name,
            )
            beatmap_mirror.score_last_updated_at = datetime.now()

    sorted_mirrors = sorted(
        BEATMAP_MIRRORS,
        key=lambda mirror: mirror.score,
        reverse=True,
    )

    for mirror in sorted_mirrors:
        try:
            result = await mirror.fetch_beatmap_zip_data(beatmapset_id)
        except Exception as exc:
            ended_at = datetime.now()
            await beatmap_mirror_requests.log_beatmap_mirror_request(
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
        # TODO: should log this case
        return None

    ended_at = datetime.now()

    await beatmap_mirror_requests.log_beatmap_mirror_request(
        request=beatmap_mirror_requests.BeatmapMirrorRequest(
            request_url=f"{mirror.base_url}/d/{beatmapset_id}",
            api_key_id=None,
            mirror_name=mirror.name,
            success=True,
            started_at=started_at,
            ended_at=ended_at,
            response_size=len(result) if result else None,
            response_error=None,
        ),
    )

    ms_elapsed = (ended_at.timestamp() - started_at.timestamp()) * 1000

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
