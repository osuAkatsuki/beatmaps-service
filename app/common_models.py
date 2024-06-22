from enum import IntEnum


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
