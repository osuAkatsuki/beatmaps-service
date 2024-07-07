import logging

import httpx
from typing_extensions import override

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
        response: httpx.Response | None = None
        try:
            response = await self.http_client.get(
                f"{self.base_url}/d/{beatmapset_id}",
            )
            if response.status_code in (404, 451):
                return BeatmapMirrorResponse(
                    data=None,
                    is_success=True,
                    request_url=str(response.request.url),
                    status_code=response.status_code,
                )
            response.raise_for_status()
            return BeatmapMirrorResponse(
                data=response.read(),
                is_success=True,
                request_url=str(response.request.url),
                status_code=response.status_code,
            )
        except Exception as exc:
            return BeatmapMirrorResponse(
                data=None,
                is_success=False,
                request_url=str(response.request.url) if response else None,
                status_code=response.status_code if response else None,
                error_message=str(exc),
            )
