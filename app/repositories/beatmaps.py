from pydantic import BaseModel

from app import state
from app.common_models import GameMode
from app.common_models import RankedStatus


class AkatsukiBeatmap(BaseModel):
    beatmap_id: int
    beatmapset_id: int
    beatmap_md5: str
    song_name: str
    file_name: str
    ar: float
    od: float
    mode: GameMode
    max_combo: int
    hit_length: int
    bpm: int
    ranked: RankedStatus
    latest_update: int
    ranked_status_freezed: bool
    playcount: int
    passcount: int
    rankedby: int | None
    rating: float
    bancho_ranked_status: RankedStatus | None
    count_circles: int | None
    count_spinners: int | None
    count_sliders: int | None
    bancho_creator_id: int | None
    bancho_creator_name: str | None


async def fetch_one_by_id(beatmap_id: int, /) -> AkatsukiBeatmap | None:
    query = """\
        SELECT * FROM beatmaps WHERE beatmap_id = :beatmap_id
    """
    rec = await state.database.fetch_one(query, {"beatmap_id": beatmap_id})
    if rec is None:
        return None
    return AkatsukiBeatmap(
        beatmap_id=rec["beatmap_id"],
        beatmapset_id=rec["beatmapset_id"],
        beatmap_md5=rec["beatmap_md5"],
        song_name=rec["song_name"],
        file_name=rec["file_name"],
        ar=rec["ar"],
        od=rec["od"],
        mode=rec["mode"],
        max_combo=rec["max_combo"],
        hit_length=rec["hit_length"],
        bpm=rec["bpm"],
        ranked=rec["ranked"],
        latest_update=rec["latest_update"],
        ranked_status_freezed=rec["ranked_status_freezed"],
        playcount=rec["playcount"],
        passcount=rec["passcount"],
        rankedby=rec["rankedby"],
        rating=rec["rating"],
        bancho_ranked_status=rec["bancho_ranked_status"],
        count_circles=rec["count_circles"],
        count_spinners=rec["count_spinners"],
        count_sliders=rec["count_sliders"],
        bancho_creator_id=rec["bancho_creator_id"],
        bancho_creator_name=rec["bancho_creator_name"],
    )


async def create(beatmap: AkatsukiBeatmap) -> AkatsukiBeatmap:
    query = """\
        INSERT INTO beatmaps (
            beatmap_id, beatmapset_id, beatmap_md5, song_name, file_name,
            ar, od, mode, max_combo, hit_length, bpm, ranked, latest_update,
            ranked_status_freezed, playcount, passcount, rankedby, rating,
            bancho_ranked_status, count_circles, count_spinners, count_sliders,
            bancho_creator_id, bancho_creator_name
        )
        VALUES (
            :beatmap_id, :beatmapset_id, :beatmap_md5, :song_name, :file_name,
            :ar, :od, :mode, :max_combo, :hit_length, :bpm, :ranked, :latest_update,
            :ranked_status_freezed, :playcount, :passcount, :rankedby, :rating,
            :bancho_ranked_status, :count_circles, :count_spinners, :count_sliders,
            :bancho_creator_id, :bancho_creator_name
        )
    """
    await state.database.execute(
        query=query,
        values={
            "beatmap_id": beatmap.beatmap_id,
            "beatmapset_id": beatmap.beatmapset_id,
            "beatmap_md5": beatmap.beatmap_md5,
            "song_name": beatmap.song_name,
            "file_name": beatmap.file_name,
            "ar": beatmap.ar,
            "od": beatmap.od,
            "mode": beatmap.mode.value,
            "max_combo": beatmap.max_combo,
            "hit_length": beatmap.hit_length,
            "bpm": beatmap.bpm,
            "ranked": beatmap.ranked.value,
            "latest_update": beatmap.latest_update,
            "ranked_status_freezed": beatmap.ranked_status_freezed,
            "playcount": beatmap.playcount,
            "passcount": beatmap.passcount,
            "rankedby": beatmap.rankedby,
            "rating": beatmap.rating,
            "bancho_ranked_status": (
                beatmap.bancho_ranked_status.value
                if beatmap.bancho_ranked_status is not None
                else None
            ),
            "count_circles": beatmap.count_circles,
            "count_spinners": beatmap.count_spinners,
            "count_sliders": beatmap.count_sliders,
            "bancho_creator_id": beatmap.bancho_creator_id,
            "bancho_creator_name": beatmap.bancho_creator_name,
        },
    )
    rec = await state.database.fetch_one(
        """\
        SELECT * FROM beatmaps WHERE beatmap_id = :beatmap_id
        """,
        {"beatmap_id": beatmap.beatmap_id},
    )
    assert rec is not None

    return AkatsukiBeatmap(
        beatmap_id=rec["beatmap_id"],
        beatmapset_id=rec["beatmapset_id"],
        beatmap_md5=rec["beatmap_md5"],
        song_name=rec["song_name"],
        file_name=rec["file_name"],
        ar=rec["ar"],
        od=rec["od"],
        mode=rec["mode"],
        max_combo=rec["max_combo"],
        hit_length=rec["hit_length"],
        bpm=rec["bpm"],
        ranked=rec["ranked"],
        latest_update=rec["latest_update"],
        ranked_status_freezed=rec["ranked_status_freezed"],
        playcount=rec["playcount"],
        passcount=rec["passcount"],
        rankedby=rec["rankedby"],
        rating=rec["rating"],
        bancho_ranked_status=rec["bancho_ranked_status"],
        count_circles=rec["count_circles"],
        count_spinners=rec["count_spinners"],
        count_sliders=rec["count_sliders"],
        bancho_creator_id=rec["bancho_creator_id"],
        bancho_creator_name=rec["bancho_creator_name"],
    )
