from abc import ABC
from dataclasses import dataclass
from typing import Any
from typing import ClassVar
from typing import Generic
from typing import TypeVar

import httpx

from app.adapters.osu_mirrors.resilience import MirrorHealth
from app.adapters.osu_mirrors.resilience import TokenBucket
from app.common_models import CheesegullBeatmap
from app.common_models import CheesegullBeatmapset
from app.repositories.beatmap_mirror_requests import MirrorResource

T = TypeVar("T", covariant=True)


@dataclass
class BeatmapMirrorResponse(Generic[T]):
    data: T
    is_success: bool
    request_url: str | None
    status_code: int | None
    error_message: str | None = None


class AbstractBeatmapMirror(ABC):
    name: ClassVar[str]
    base_url: ClassVar[str]
    supported_resources: ClassVar[set[MirrorResource]]
    requests_per_second: ClassVar[float | None] = None  # Rate limit, if known

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.http_client = httpx.AsyncClient(
            headers={"User-Agent": "Akatsuki-Beatmaps-Service/1.0"},
            timeout=httpx.Timeout(10.0, connect=5.0),
            follow_redirects=True,
        )
        # Initialize health tracking with optional rate limiter
        rate_limiter = None
        if self.requests_per_second is not None:
            rate_limiter = TokenBucket(
                tokens_per_second=self.requests_per_second,
                bucket_size=self.requests_per_second * 2,  # Allow small bursts
            )
        self.health = MirrorHealth(rate_limiter=rate_limiter)
        super().__init__(*args, **kwargs)

    async def fetch_one_cheesegull_beatmap(
        self,
        beatmap_id: int,
    ) -> BeatmapMirrorResponse[CheesegullBeatmap | None]:
        """Fetch a cheesegull beatmap from a beatmap mirror."""
        raise NotImplementedError()

    async def fetch_one_cheesegull_beatmapset(
        self,
        beatmapset_id: int,
    ) -> BeatmapMirrorResponse[CheesegullBeatmapset | None]:
        """Fetch a cheesegull beatmapset from a beatmap mirror."""
        raise NotImplementedError()

    async def fetch_beatmap_zip_data(
        self,
        beatmapset_id: int,
    ) -> BeatmapMirrorResponse[bytes | None]:
        """Fetch a beatmap's .osz file content from a beatmap mirror."""
        raise NotImplementedError()

    async def fetch_beatmap_background_image(
        self,
        beatmap_id: int,
    ) -> BeatmapMirrorResponse[bytes | None]:
        """Fetch a beatmap's background image from a beatmap mirror."""
        raise NotImplementedError()
