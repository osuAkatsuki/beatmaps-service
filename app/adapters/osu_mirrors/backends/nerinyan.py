from typing_extensions import override

from app.adapters.osu_mirrors.backends import MAX_RESPONSE_BYTES
from app.adapters.osu_mirrors.backends import AbstractBeatmapMirror
from app.adapters.osu_mirrors.backends import BeatmapMirrorResponse
from app.repositories.beatmap_mirror_requests import MirrorResource


class NerinyanMirror(AbstractBeatmapMirror):
    name = "nerinyan"
    base_url = "https://api.nerinyan.moe"
    supported_resources = {MirrorResource.OSZ_FILE}

    @override
    async def fetch_beatmap_zip_data(
        self,
        beatmapset_id: int,
    ) -> BeatmapMirrorResponse[bytes | None]:
        return await self._fetch(
            f"{self.base_url}/d/{beatmapset_id}",
            lambda r: r.read(),
            max_response_bytes=MAX_RESPONSE_BYTES,
        )
