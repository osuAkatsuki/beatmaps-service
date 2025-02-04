from datetime import datetime
from enum import IntEnum

from pydantic import BaseModel


class RankedStatus(IntEnum):
    NOT_SUBMITTED = -1
    PENDING = 0
    UPDATE_AVAILABLE = 1
    RANKED = 2
    APPROVED = 3
    QUALIFIED = 4
    LOVED = 5

    def osu_api(self) -> int | None:
        return {
            self.PENDING: 0,
            self.RANKED: 1,
            self.APPROVED: 2,
            self.QUALIFIED: 3,
            self.LOVED: 4,
        }.get(self)

    @classmethod
    def from_osu_api(cls, osu_api_status: int) -> "RankedStatus":
        return {
            -2: cls.PENDING,  # graveyard
            -1: cls.PENDING,  # wip
            0: cls.PENDING,
            1: cls.RANKED,
            2: cls.APPROVED,
            3: cls.QUALIFIED,
            4: cls.LOVED,
        }.get(osu_api_status, cls.UPDATE_AVAILABLE)

    @classmethod
    def from_direct(cls, direct_status: int) -> "RankedStatus":
        return {
            0: cls.RANKED,
            2: cls.PENDING,
            3: cls.QUALIFIED,
            5: cls.PENDING,  # graveyard
            7: cls.RANKED,  # played before
            8: cls.LOVED,
        }.get(direct_status, cls.UPDATE_AVAILABLE)


class OsuDirectRankedStatus(IntEnum):
    ALL = 4
    RANKED = 0
    RANKED_PLAYED = 7
    LOVED = 8
    QUALIFIED = 3
    PENDING = 2
    GRAVEYARD = 5


class GameMode(IntEnum):
    OSU = 0
    TAIKO = 1
    FRUITS = 2
    MANIA = 3


class CheesegullRankedStatus(IntEnum):
    # This is a limited subset of the osu! api ranked status
    PENDING = 0
    RANKED = 1
    APPROVED = 2
    QUALIFIED = 3
    LOVED = 4


class CheesegullBeatmap(BaseModel):
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


class CheesegullBeatmapset(BaseModel):
    SetID: int
    ChildrenBeatmaps: list[CheesegullBeatmap]
    RankedStatus: int
    ApprovedDate: datetime
    LastUpdate: datetime
    LastChecked: datetime
    Artist: str
    Title: str
    Creator: str
    Source: str
    Tags: str
    HasVideo: bool
    Genre: int | None
    Language: int | None
    Favourites: int
