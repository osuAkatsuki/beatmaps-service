import logging

import httpx
from typing_extensions import override

from app import settings
from app.adapters.osu_mirrors.backends import AbstractBeatmapMirror
from app.adapters.osu_mirrors.backends import BeatmapMirrorResponse
from app.repositories.beatmap_mirror_requests import MirrorResource


class MinoMirror(AbstractBeatmapMirror):
    name = "mino"
    base_url = "https://catboy.best"
    supported_resources = {MirrorResource.OSZ_FILE, MirrorResource.BACKGROUND_IMAGE}

    @override
    async def fetch_beatmap_zip_data(
        self,
        beatmapset_id: int,
    ) -> BeatmapMirrorResponse[bytes | None]:
        response: httpx.Response | None = None
        try:
            response = await self.http_client.get(
                f"{self.base_url}/d/{beatmapset_id}",
                headers={"x-ratelimit-key": settings.MINO_INCREASED_RATELIMIT_KEY},
                timeout=httpx.Timeout(None, connect=2),
            )
            if response.status_code == 404:
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

    @override
    async def fetch_beatmap_background_image(
        self,
        beatmap_id: int,
    ) -> BeatmapMirrorResponse[bytes | None]:
        response: httpx.Response | None = None
        try:
            logging.info(f"Fetching beatmap background from mino: {beatmap_id}")
            response = await self.http_client.get(
                f"{self.base_url}/preview/background/{beatmap_id}",
                timeout=httpx.Timeout(None, connect=2),
            )
            if response.status_code == 404:
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
            logging.warning(
                "Failed to fetch beatmap background from catboy.best",
                exc_info=True,
            )
            return BeatmapMirrorResponse(
                data=None,
                is_success=False,
                request_url=str(response.request.url) if response else None,
                status_code=response.status_code if response else None,
                error_message=str(exc),
            )


class MinoCentralMirror(MinoMirror):
    name = "mino-central"
    base_url = "https://central.catboy.best"


class MinoUSMirror(MinoMirror):
    name = "mino-us"
    base_url = "https://us.catboy.best"
