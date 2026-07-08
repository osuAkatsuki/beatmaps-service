from typing_extensions import override

from app import settings
from app.adapters.osu_mirrors.backends import MAX_RESPONSE_BYTES
from app.adapters.osu_mirrors.backends import AbstractBeatmapMirror
from app.adapters.osu_mirrors.backends import BeatmapMirrorResponse
from app.repositories.beatmap_mirror_requests import MirrorResource


class MinoMirror(AbstractBeatmapMirror):
    name = "mino"
    base_url = "https://catboy.best"
    supported_resources = {MirrorResource.OSZ_FILE, MirrorResource.BACKGROUND_IMAGE}

    @override
    def _extra_headers(self) -> dict[str, str]:
        return {"x-ratelimit-key": settings.MINO_INCREASED_RATELIMIT_KEY}

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

    @override
    async def fetch_beatmap_background_image(
        self,
        beatmap_id: int,
    ) -> BeatmapMirrorResponse[bytes | None]:
        return await self._fetch(
            f"{self.base_url}/preview/background/{beatmap_id}",
            lambda r: r.read(),
        )


class MinoCentralMirror(MinoMirror):
    name = "mino-germany"
    base_url = "https://central.catboy.best"


class MinoUSMirror(MinoMirror):
    name = "mino-us"
    base_url = "https://us.catboy.best"


class MinoSingaporeMirror(MinoMirror):
    name = "mino-singapore"
    base_url = "https://sg.catboy.best"
