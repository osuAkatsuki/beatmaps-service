from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import ClassVar

import httpx


class MirrorRequestError(Exception):
    pass


class AbstractBeatmapMirror(ABC):
    name: ClassVar[str]
    base_url: ClassVar[str]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.http_client = httpx.AsyncClient()
        self.weight = 0
        super().__init__(*args, **kwargs)

    @abstractmethod
    async def fetch_beatmap_zip_data(self, beatmapset_id: int) -> bytes | None:
        """Fetch a beatmap's .osz2 file content from a beatmap mirror."""
        pass
