import logging
import time

from app.adapters import aws_s3
from app.adapters import discord_webhooks
from app.adapters import osu_api_v1
from app.common_models import RankedStatus
from app.repositories import akatsuki_beatmaps
from app.repositories.akatsuki_beatmaps import AkatsukiBeatmap

IGNORED_BEATMAP_CHARS = dict.fromkeys(map(ord, r':\/*<>?"|'), None)
FROZEN_STATUSES = {RankedStatus.RANKED, RankedStatus.APPROVED, RankedStatus.LOVED}


def _parse_akatsuki_beatmap_from_osu_api_v1_response(
    osu_api_beatmap: osu_api_v1.Beatmap,
) -> AkatsukiBeatmap:
    filename = (
        ("{artist} - {title} ({creator}) [{version}].osu")
        .format(
            artist=osu_api_beatmap.artist,
            title=osu_api_beatmap.title,
            creator=osu_api_beatmap.creator,
            version=osu_api_beatmap.version,
        )
        .translate(IGNORED_BEATMAP_CHARS)
    )

    song_name = (
        ("{artist} - {title} [{version}]")
        .format(
            artist=osu_api_beatmap.artist,
            title=osu_api_beatmap.title,
            version=osu_api_beatmap.version,
        )
        .translate(IGNORED_BEATMAP_CHARS)
    )

    bancho_ranked_status = RankedStatus.from_osu_api(osu_api_beatmap.approved)
    frozen = bancho_ranked_status in FROZEN_STATUSES

    akatsuki_beatmap = AkatsukiBeatmap(
        beatmap_md5=osu_api_beatmap.file_md5,
        beatmap_id=osu_api_beatmap.beatmap_id,
        beatmapset_id=osu_api_beatmap.beatmapset_id,
        song_name=song_name,
        ranked=bancho_ranked_status,
        playcount=0,
        passcount=0,
        mode=osu_api_beatmap.mode,
        od=osu_api_beatmap.diff_overall,
        ar=osu_api_beatmap.diff_approach,
        hit_length=osu_api_beatmap.hit_length,
        latest_update=int(time.time()),
        max_combo=osu_api_beatmap.max_combo or 0,
        bpm=round(osu_api_beatmap.bpm) if osu_api_beatmap.bpm is not None else 0,
        file_name=filename,
        ranked_status_freezed=frozen,
        rankedby=None,
        rating=10.0,
        bancho_ranked_status=bancho_ranked_status,
        count_circles=osu_api_beatmap.count_normal,
        count_sliders=osu_api_beatmap.count_slider,
        count_spinners=osu_api_beatmap.count_spinner,
        bancho_creator_id=osu_api_beatmap.creator_id,
        bancho_creator_name=osu_api_beatmap.creator,
    )
    return akatsuki_beatmap


async def _update_from_osu_api(old_beatmap: AkatsukiBeatmap) -> AkatsukiBeatmap | None:
    if not old_beatmap.deserves_update:
        return old_beatmap

    new_osu_api_v1_beatmap = await osu_api_v1.fetch_one_beatmap(
        beatmap_id=old_beatmap.beatmap_id,
    )
    if new_osu_api_v1_beatmap is None:
        # The map has been unsubmitted by the mapper or staff
        # on the official osu! servers. We'll delete it as well.
        logging.info(
            "Deleting unsubmitted beatmap",
            extra={"beatmap": old_beatmap.model_dump()},
        )
        await akatsuki_beatmaps.delete_by_md5(old_beatmap.beatmap_md5)
        await aws_s3.delete_object(f"/beatmaps/{old_beatmap.beatmap_id}.osu")
        return None

    new_beatmap = _parse_akatsuki_beatmap_from_osu_api_v1_response(
        new_osu_api_v1_beatmap,
    )

    # handle deleting the old beatmap etc.
    if new_beatmap.beatmap_md5 != old_beatmap.beatmap_md5:
        # delete any instances of the old map
        logging.info(
            "Deleting old beatmap",
            extra={"old_beatmap": old_beatmap.model_dump()},
        )
        await akatsuki_beatmaps.delete_by_md5(old_beatmap.beatmap_md5)
    else:
        # the map may have changed in some ways (e.g. ranked status),
        # but we want to make sure to keep our stats, because the map
        # is the same from the player's pov (hit objects, ar/od, etc.)
        new_beatmap.playcount = old_beatmap.playcount
        new_beatmap.passcount = old_beatmap.passcount
        new_beatmap.rating = old_beatmap.rating
        new_beatmap.rankedby = old_beatmap.rankedby

    if old_beatmap.ranked_status_freezed:
        # if the previous version is status frozen
        # we should force the old status on the new version
        new_beatmap.ranked = old_beatmap.ranked
        new_beatmap.ranked_status_freezed = True
        new_beatmap.rankedby = old_beatmap.rankedby
    elif old_beatmap.ranked != new_beatmap.ranked:
        if new_beatmap.ranked is RankedStatus.PENDING and old_beatmap.ranked in {
            RankedStatus.RANKED,
            RankedStatus.APPROVED,
            RankedStatus.LOVED,
        }:
            discord_webhooks.beatmap_status_change(
                old_beatmap=old_beatmap,
                new_beatmap=new_beatmap,
                action_taken="frozen",
            )
            new_beatmap.ranked = old_beatmap.ranked
            new_beatmap.ranked_status_freezed = True
        else:
            discord_webhooks.beatmap_status_change(
                old_beatmap=old_beatmap,
                new_beatmap=new_beatmap,
                action_taken="status_change",
            )

    new_beatmap.latest_update = int(time.time())

    new_beatmap = await akatsuki_beatmaps.create_or_replace(new_beatmap)

    # invalidate any cached .osu data in s3
    await aws_s3.delete_object(f"/beatmaps/{new_beatmap.beatmap_id}.osu")

    return new_beatmap


async def fetch_one_by_id(beatmap_id: int) -> AkatsukiBeatmap | None:
    beatmap = await akatsuki_beatmaps.fetch_one_by_id(beatmap_id)
    if beatmap is None:
        osu_api_v1_beatmap = await osu_api_v1.fetch_one_beatmap(beatmap_id=beatmap_id)
        if osu_api_v1_beatmap is None:
            return None

        new_beatmap = _parse_akatsuki_beatmap_from_osu_api_v1_response(
            osu_api_v1_beatmap,
        )
        beatmap = await akatsuki_beatmaps.create_or_replace(new_beatmap)

    elif beatmap.deserves_update:
        try:
            beatmap = await _update_from_osu_api(beatmap)
            if beatmap is None:
                # (we may have deleted the map during the update)
                return None
        except Exception:
            logging.warning(
                "Failed to update beatmap requested by id (using old beatmap for now)",
                extra={
                    "beatmap": beatmap.model_dump() if beatmap else None,
                    "beatmap_id": beatmap_id,
                },
            )

    return beatmap


async def fetch_one_by_md5(beatmap_md5: str) -> AkatsukiBeatmap | None:
    beatmap = await akatsuki_beatmaps.fetch_one_by_md5(beatmap_md5)
    if beatmap is None:
        osu_api_v1_beatmap = await osu_api_v1.fetch_one_beatmap(beatmap_md5=beatmap_md5)
        if osu_api_v1_beatmap is None:
            return None

        new_beatmap = _parse_akatsuki_beatmap_from_osu_api_v1_response(
            osu_api_v1_beatmap,
        )
        beatmap = await akatsuki_beatmaps.create_or_replace(new_beatmap)

    elif beatmap.deserves_update:
        try:
            beatmap = await _update_from_osu_api(beatmap)
            if beatmap is None:
                # (we may have deleted the map during the update)
                return None
        except Exception:
            logging.warning(
                "Failed to update beatmap requested by md5 (using old beatmap for now)",
                extra={
                    "beatmap": beatmap.model_dump() if beatmap else None,
                    "beatmap_md5": beatmap_md5,
                },
            )

    return beatmap
