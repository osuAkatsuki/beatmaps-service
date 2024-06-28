import logging

import httpx

from app.adapters.osu_mirrors.backends import AbstractBeatmapMirror
from app.adapters.osu_mirrors.backends import MirrorRequestError


class OsuDirectMirror(AbstractBeatmapMirror):
    name = "osu_direct"
    base_url = "https://osu.direct"

    async def fetch_beatmap_zip_data(self, beatmapset_id: int) -> bytes | None:
        try:
            logging.info(f"Fetching beatmapset osz2 from osu!direct: {beatmapset_id}")
            response = await self.http_client.get(
                f"{self.base_url}/api/d/{beatmapset_id}",
                timeout=httpx.Timeout(None, connect=2),
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.read()
        except Exception as exc:
            logging.warning(
                "Failed to fetch beatmap from osu!direct",
                exc_info=True,
            )
            raise MirrorRequestError() from exc
