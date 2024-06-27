import logging

from app.adapters.osu_mirrors.backends import AbstractBeatmapMirror
from app.adapters.osu_mirrors.backends import MirrorRequestError


class GatariMirror(AbstractBeatmapMirror):
    name = "gatari"
    base_url = "https://osu.gatari.pw"

    async def fetch_beatmap_zip_data(self, beatmapset_id: int) -> bytes | None:
        try:
            logging.info(f"Fetching beatmapset osz2 from gatari: {beatmapset_id}")
            response = await self.http_client.get(
                f"{self.base_url}/d/{beatmapset_id}",
                follow_redirects=True,
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.read()
        except Exception as exc:
            logging.warning(
                "Failed to fetch beatmap from gatari.pw",
                exc_info=True,
            )
            raise MirrorRequestError() from exc
