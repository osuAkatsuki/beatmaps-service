import logging

from app.adapters.osu_mirrors.backends import AbstractBeatmapMirror


class NerinyanMirror(AbstractBeatmapMirror):
    name = "nerinyan"
    base_url = "https://api.nerinyan.moe"

    async def fetch_beatmap_zip_data(self, beatmapset_id: int) -> bytes | None:
        try:
            logging.info(f"Fetching beatmapset osz2 from nerinyan: {beatmapset_id}")
            response = await self.http_client.get(
                f"{self.base_url}/d/{beatmapset_id}",
            )
            response.raise_for_status()
            return response.read()
        except Exception:
            logging.warning(
                "Failed to fetch beatmap from nerinyan.moe",
                exc_info=True,
            )
            return None
