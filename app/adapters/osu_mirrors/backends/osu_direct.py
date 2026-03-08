from typing_extensions import override

from app.adapters.osu_mirrors.backends import MAX_RESPONSE_BYTES
from app.adapters.osu_mirrors.backends import AbstractBeatmapMirror
from app.adapters.osu_mirrors.backends import BeatmapMirrorResponse
from app.common_models import CheesegullBeatmap
from app.common_models import CheesegullBeatmapset
from app.repositories.beatmap_mirror_requests import MirrorResource


class OsuDirectMirror(AbstractBeatmapMirror):
    name = "osu_direct"
    base_url = "https://osu.direct"
    supported_resources = {MirrorResource.OSZ_FILE, MirrorResource.BACKGROUND_IMAGE}

    @override
    async def fetch_one_cheesegull_beatmap(
        self,
        beatmap_id: int,
    ) -> BeatmapMirrorResponse[CheesegullBeatmap | None]:
        return await self._fetch(
            f"{self.base_url}/api/b/{beatmap_id}",
            lambda r: CheesegullBeatmap.model_validate(r.json()),
        )

    @override
    async def fetch_one_cheesegull_beatmapset(
        self,
        beatmapset_id: int,
    ) -> BeatmapMirrorResponse[CheesegullBeatmapset | None]:
        return await self._fetch(
            f"{self.base_url}/api/s/{beatmapset_id}",
            lambda r: CheesegullBeatmapset.model_validate(r.json()),
        )

    @override
    async def fetch_beatmap_zip_data(
        self,
        beatmapset_id: int,
    ) -> BeatmapMirrorResponse[bytes | None]:
        return await self._fetch(
            f"{self.base_url}/api/d/{beatmapset_id}",
            lambda r: r.read(),
            max_response_bytes=MAX_RESPONSE_BYTES,
        )

    @override
    async def fetch_beatmap_background_image(
        self,
        beatmap_id: int,
    ) -> BeatmapMirrorResponse[bytes | None]:
        return await self._fetch(
            f"{self.base_url}/api/media/background/{beatmap_id}",
            lambda r: r.read(),
        )
