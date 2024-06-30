from abc import ABC
from dataclasses import dataclass
from typing import Any
from typing import ClassVar
from typing import Generic
from typing import TypeVar

import httpx

from app.repositories.beatmap_mirror_requests import MirrorResource

T = TypeVar("T", covariant=True)


class MirrorRequestError(Exception):
    pass


@dataclass
class BeatmapMirrorResponse(Generic[T]):
    data: T
    request_url: str
    status_code: int


class AbstractBeatmapMirror(ABC):
    name: ClassVar[str]
    base_url: ClassVar[str]
    supported_resources: ClassVar[set[MirrorResource]]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.http_client = httpx.AsyncClient()
        self.weight = 0
        super().__init__(*args, **kwargs)

    async def fetch_beatmap_zip_data(
        self,
        beatmapset_id: int,
    ) -> BeatmapMirrorResponse[bytes | None]:
        """Fetch a beatmap's .osz2 file content from a beatmap mirror."""
        raise NotImplementedError()

    async def fetch_beatmap_background_image(
        self,
        beatmap_id: int,
    ) -> BeatmapMirrorResponse[bytes | None]:
        """Fetch a beatmap's background image from a beatmap mirror."""
        raise NotImplementedError()
