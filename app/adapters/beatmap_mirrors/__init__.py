from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import ClassVar

import httpx


class BeatmapMirror(ABC):
    base_url: ClassVar[str]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.http_client = httpx.AsyncClient()
        super().__init__(*args, **kwargs)

    @abstractmethod
    async def fetch_beatmap_zip_data(self, beatmapset_id: int) -> bytes | None:
        """Fetch a beatmap's .osz2 file content from a beatmap mirror."""
        pass
