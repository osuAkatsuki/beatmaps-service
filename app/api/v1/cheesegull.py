from fastapi import APIRouter
from pydantic import BaseModel

from app.adapters import osu_api_v2

router = APIRouter()


class CheesegullBeatmap(BaseModel):
    # BeatmapID: 315,
    # ParentSetID: 141,
    # DiffName: "Insane",
    # FileMD5: "1cf5b2c2edfafd055536d2cefcb89c0e",
    # Mode: 0,
    # BPM: 168,
    # AR: 7,
    # OD: 7,
    # CS: 6,
    # HP: 2,
    # TotalLength: 14,
    # HitLength: 14,
    # Playcount: 1767740,
    # Passcount: 1074297,
    # MaxCombo: 114,
    # DifficultyRating: 5.23
    BeatmapID: int
    ParentSetID: int
    DiffName: str
    FileMD5: str
    Mode: int
    BPM: float
    AR: float
    OD: float
    CS: float
    HP: float
    TotalLength: int
    HitLength: int
    Playcount: int
    Passcount: int
    MaxCombo: int
    DifficultyRating: float


@router.get("/api/v1/cheesegull/b/{beatmap_id}")
async def cheesegull_beatmap(beatmap_id: int):
    osu_api_beatmap = await osu_api_v2.get_beatmap(beatmap_id)
    cheesegull_beatmap = CheesegullBeatmap(
        BeatmapID=osu_api_beatmap.id,
        ParentSetID=osu_api_beatmap.beatmapset_id,
        DiffName=osu_api_beatmap.version,
        FileMD5=osu_api_beatmap.checksum or "",
        Mode=osu_api_beatmap.mode_int,
        BPM=osu_api_beatmap.bpm or 0,
        AR=osu_api_beatmap.ar,
        OD=osu_api_beatmap.accuracy,
        CS=osu_api_beatmap.cs,
        HP=osu_api_beatmap.drain,
        TotalLength=osu_api_beatmap.total_length,
        HitLength=osu_api_beatmap.total_length,
        Playcount=osu_api_beatmap.playcount,
        Passcount=osu_api_beatmap.passcount,
        MaxCombo=osu_api_beatmap.max_combo,
        DifficultyRating=osu_api_beatmap.difficulty_rating,
    )
    return cheesegull_beatmap.model_dump()


@router.get("/api/v1/cheesegull/s/{beatmapset_id}")
async def cheesegull_beatmapset(beatmapset_id: int):
    return {"beatmapset_id": beatmapset_id}
