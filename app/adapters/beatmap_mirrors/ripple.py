import logging

from app.adapters.beatmap_mirrors import BeatmapMirror


class RippleMirror(BeatmapMirror):
    base_url = "https://storage.ripple.moe"

    async def fetch_beatmap_zip_data(self, beatmapset_id: int) -> bytes | None:
        try:
            logging.info(f"Fetching beatmapset osz2 from ripple: {beatmapset_id}")
            response = await self.http_client.get(
                f"{self.base_url}/d/{beatmapset_id}",
            )
            response.raise_for_status()
            return response.read()
        except Exception:
            logging.warning(
                "Failed to fetch beatmap from ripple.moe",
                exc_info=True,
            )
            return None
