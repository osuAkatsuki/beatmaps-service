import logging

from app.adapters.osu_mirrors.backends import AbstractBeatmapMirror
from app.adapters.osu_mirrors.backends import MirrorRequestError


class NerinyanMirror(AbstractBeatmapMirror):
    name = "nerinyan"
    base_url = "https://api.nerinyan.moe"

    async def fetch_beatmap_zip_data(self, beatmapset_id: int) -> bytes | None:
        try:
            logging.info(f"Fetching beatmapset osz2 from nerinyan: {beatmapset_id}")
            response = await self.http_client.get(
                f"{self.base_url}/d/{beatmapset_id}",
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.read()
        except Exception as exc:
            logging.warning(
                "Failed to fetch beatmap from nerinyan.moe",
                exc_info=True,
            )
            raise MirrorRequestError() from exc
