from datetime import datetime
from enum import IntEnum
from enum import StrEnum
from typing import Any

from pydantic import BaseModel
from pydantic import Field

from app.common_models import RankedStatus


class Ruleset(StrEnum):
    OSU = "osu"
    TAIKO = "taiko"
    FRUITS = "fruits"
    MANIA = "mania"


class Failtimes(BaseModel):
    exit: list[int]  # TODO: nullable? osu api says yes
    fail: list[int]  # TODO: nullable? osu api says yes


class Beatmap(BaseModel):
    beatmapset_id: int
    difficulty_rating: float
    id: int
    mode: Ruleset
    status: str  # ranked status (TODO enum?)
    total_length: int
    user_id: int
    version: str

    # TODO: enable this, if desired
    # - Beatmapset for Beatmap objects
    # - BeatmapsetExtended for BeatmapExtended objects
    # - None if there is no associated set (e.g. deleted)
    # beatmapset: Beatmapset | BeatmapsetExtended | None

    checksum: str | None
    failtimes: Failtimes | None = None
    max_combo: int | None = None
    bpm: float


class BeatmapExtended(Beatmap):
    accuracy: float
    ar: float
    beatmapset_id: int
    convert: bool
    count_circles: int
    count_sliders: int
    count_spinners: int
    cs: float
    deleted_at: datetime | None
    drain: float
    hit_length: int
    is_scoreable: bool
    last_updated: datetime
    mode_int: int
    passcount: int
    playcount: int
    ranked: int  # TODO: enum
    url: str


class Covers(BaseModel):
    cover: str
    cover2x: str = Field(alias="cover@2x")
    card: str
    card2x: str = Field(alias="card@2x")
    list: str
    list2x: str = Field(alias="list@2x")
    slimcover: str
    slimcover2x: str = Field(alias="slimcover@2x")


class RequiredMeta(BaseModel):
    main_ruleset: int
    non_main_ruleset: int


class NominationsSummary(BaseModel):
    current: int
    eligible_main_rulesets: list[Ruleset] | None = None
    required_meta: RequiredMeta


class Availability(BaseModel):
    download_disabled: bool
    more_information: str | None


class GenreId(IntEnum):
    UNSPECIFIED = 1
    VIDEO_GAME = 2
    ANIME = 3
    ROCK = 4
    POP = 5
    OTHER = 6
    NOVELTY = 7
    HIP_HOP = 9
    ELECTRONIC = 10
    METAL = 11
    CLASSICAL = 12
    FOLK = 13
    JAZZ = 14


class Genre(BaseModel):
    id: GenreId
    name: str


class Description(BaseModel):
    description: str  # (html string)


class LanguageId(IntEnum):
    UNSPECIFIED = 1
    ENGLISH = 2
    JAPANESE = 3
    CHINESE = 4
    INSTRUMENTAL = 5
    KOREAN = 6
    FRENCH = 7
    GERMAN = 8
    SWEDISH = 9
    SPANISH = 10
    ITALIAN = 11
    RUSSIAN = 12
    POLISH = 13
    OTHER = 14


class Language(BaseModel):
    id: LanguageId
    name: str


class Beatmapset(BaseModel):
    artist: str
    artist_unicode: str | None
    covers: Covers
    creator: str
    favourite_count: int
    hype: Any | None  # TODO
    id: int
    nsfw: bool
    offset: int
    play_count: int
    preview_url: str
    source: str
    spotlight: bool
    status: str  # TODO enum
    title: str
    title_unicode: str | None
    user_id: int
    video: bool


class BeatmapsetExtended(Beatmapset):
    bpm: float | None
    can_be_hyped: bool
    deleted_at: datetime | None
    discussion_enabled: bool
    discussion_locked: bool
    is_scoreable: bool
    last_updated: datetime
    legacy_thread_url: str
    nominations_summary: NominationsSummary
    ranked: int  # TODO: enum
    ranked_date: datetime | None
    storyboard: bool
    submitted_date: datetime
    tags: str

    availability: Availability

    beatmaps: list[BeatmapExtended] | None
    converts: list[BeatmapExtended] | None = None
    current_nominations: list[Any] | None = None
    current_user_attributes: Any | None = None  # TODO
    description: Description | None = None
    discussions: Any = None  # TODO
    events: Any | None = None  # TODO
    genre: Genre | None = None
    has_favourited: Any = None  # TODO
    language: Language | None = None
    pack_tags: list[str] | None
    ratings: Any | None = None  # TODO
    recent_favourites: Any | None = None  # TODO
    related_users: Any | None = None  # TODO
    user: Any | None = None  # TODO
    track_id: int | None


class Cursor(BaseModel):
    approved_date: int | None = None
    score: float | None = Field(None, alias="_score")
    id: int


class Search(BaseModel):
    sort: str  # TODO: enum


class BeatmapsetSearchResponse(BaseModel):
    beatmapsets: list[BeatmapsetExtended]
    cursor: Cursor
    cursor_string: str
    error: Any | None
    recommended_difficulty: float | None
    search: Search
    total: int


class GeneralSetting(StrEnum):
    RECOMMENDED = "recommended"
    CONVERTS = "converts"
    FOLLOWS = "follows"
    SPOTLIGHTS = "spotlights"
    FEATURED_ARTISTS = "featured_artists"


class Category(IntEnum):
    RANKED = 0
    FAVOURITES = 2
    QUALIFIED = 3
    PENDING = 4
    GRAVEYARD = 5
    MINE = 6
    ANY = 7
    LOVED = 8

    @classmethod
    def from_ranked_status(
        cls,
        osu_api_status: RankedStatus,
    ) -> "Category | None":
        return {
            RankedStatus.NOT_SUBMITTED: None,
            RankedStatus.PENDING: Category.PENDING,
            RankedStatus.UPDATE_AVAILABLE: None,
            RankedStatus.RANKED: Category.RANKED,
            RankedStatus.APPROVED: Category.RANKED,
            RankedStatus.QUALIFIED: Category.QUALIFIED,
            RankedStatus.LOVED: Category.LOVED,
        }.get(osu_api_status)


class SortBy(StrEnum):
    ARTIST_ASC = "title_asc"
    ARTIST_DESC = "title_desc"
    DIFFICULTY_ASC = "artist_asc"
    DIFFICULTY_DESC = "artist_desc"
    FAVOURITES_ASC = "difficulty_asc"
    FAVOURITES_DESC = "difficulty_desc"
    PLAYS_ASC = "ranked_asc"
    PLAYS_DESC = "ranked_desc"
    RANKED_ASC = "rating_asc"
    RANKED_DESC = "rating_desc"
    RATING_ASC = "plays_asc"
    RATING_DESC = "plays_desc"
    TITLE_ASC = "favourites_asc"
    TITLE_DES = "favourites_desc"


class Extra(StrEnum):
    VIDEO = "video"
    STORYBOARD = "storyboard"
