import logging

import httpx
from typing_extensions import override

from app.adapters.osu_mirrors.backends import AbstractBeatmapMirror
from app.adapters.osu_mirrors.backends import BeatmapMirrorResponse
from app.adapters.osu_mirrors.backends import MirrorRequestError
from app.repositories.beatmap_mirror_requests import MirrorResource


class OsuDirectMirror(AbstractBeatmapMirror):
    name = "osu_direct"
    base_url = "https://osu.direct"
    supported_resources = {MirrorResource.OSZ_FILE, MirrorResource.BACKGROUND_IMAGE}

    @override
    async def fetch_beatmap_zip_data(
        self,
        beatmapset_id: int,
    ) -> BeatmapMirrorResponse[bytes | None]:
        try:
            logging.info(f"Fetching beatmapset osz from osu!direct: {beatmapset_id}")
            response = await self.http_client.get(
                f"{self.base_url}/api/d/{beatmapset_id}",
                timeout=httpx.Timeout(None, connect=2),
            )
            if response.status_code == 404:
                return BeatmapMirrorResponse(
                    data=None,
                    request_url=str(response.request.url),
                    status_code=response.status_code,
                )
            response.raise_for_status()
            return BeatmapMirrorResponse(
                data=response.read(),
                request_url=str(response.request.url),
                status_code=response.status_code,
            )
        except Exception as exc:
            logging.warning(
                "Failed to fetch beatmap from osu!direct",
                exc_info=True,
            )
            raise MirrorRequestError() from exc

    @override
    async def fetch_beatmap_background_image(
        self,
        beatmap_id: int,
    ) -> BeatmapMirrorResponse[bytes | None]:
        try:
            logging.info(f"Fetching beatmap background from mino: {beatmap_id}")
            response = await self.http_client.get(
                f"{self.base_url}/api/media/background/{beatmap_id}",
                timeout=httpx.Timeout(None, connect=2),
            )
            if response.status_code == 404:
                return BeatmapMirrorResponse(
                    data=None,
                    request_url=str(response.request.url),
                    status_code=response.status_code,
                )
            response.raise_for_status()
            return BeatmapMirrorResponse(
                data=response.read(),
                request_url=str(response.request.url),
                status_code=response.status_code,
            )
        except Exception as exc:
            logging.warning(
                "Failed to fetch beatmap background from catboy.best",
                exc_info=True,
            )
            raise MirrorRequestError() from exc
