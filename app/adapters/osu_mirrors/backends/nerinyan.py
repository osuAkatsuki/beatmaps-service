import logging

from typing_extensions import override

from app.adapters.osu_mirrors.backends import AbstractBeatmapMirror
from app.adapters.osu_mirrors.backends import BeatmapMirrorResponse
from app.adapters.osu_mirrors.backends import MirrorRequestError
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
        try:
            logging.info(f"Fetching beatmapset osz from nerinyan: {beatmapset_id}")
            response = await self.http_client.get(
                f"{self.base_url}/d/{beatmapset_id}",
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
                "Failed to fetch beatmap from nerinyan.moe",
                exc_info=True,
            )
            raise MirrorRequestError() from exc
