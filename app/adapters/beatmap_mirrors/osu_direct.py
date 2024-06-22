import logging

import httpx

from app.adapters.beatmap_mirrors import BeatmapMirror


class OsuDirectMirror(BeatmapMirror):
    name = "osu_direct"
    base_url = "https://api.osu.direct"

    async def fetch_beatmap_zip_data(self, beatmapset_id: int) -> bytes | None:
        try:
            logging.info(f"Fetching beatmapset osz2 from osu!direct: {beatmapset_id}")
            response = await self.http_client.get(
                f"{self.base_url}/d/{beatmapset_id}",
                timeout=httpx.Timeout(None, connect=2),
            )
            response.raise_for_status()
            return response.read()
        except Exception:
            logging.warning(
                "Failed to fetch beatmap from osu!direct",
                exc_info=True,
            )
            return None
