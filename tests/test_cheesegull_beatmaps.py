import os
import unittest
from unittest.mock import AsyncMock
from unittest.mock import patch

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("APP_HOST", "127.0.0.1")
os.environ.setdefault("APP_PORT", "8081")
os.environ.setdefault("CODE_HOTRELOAD", "false")
os.environ.setdefault("OSU_API_V2_CLIENT_ID", "test")
os.environ.setdefault("OSU_API_V2_CLIENT_SECRET", "test")
os.environ.setdefault("OSU_API_V1_API_KEYS_POOL", "test")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASS", "test")
os.environ.setdefault("DB_HOST", "127.0.0.1")
os.environ.setdefault("DB_PORT", "3306")
os.environ.setdefault("DB_NAME", "test")
os.environ.setdefault("AWS_S3_ENDPOINT_URL", "test")
os.environ.setdefault("AWS_S3_REGION_NAME", "test")
os.environ.setdefault("AWS_S3_BUCKET_NAME", "test")
os.environ.setdefault("AWS_S3_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_S3_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("DISCORD_BEATMAP_UPDATES_WEBHOOK_URL", "test")
os.environ.setdefault("MINO_INCREASED_RATELIMIT_KEY", "test")

from app.adapters.osu_api_backoff import OsuApiBackoffError
from app.usecases import cheesegull_beatmaps


class CheesegullBeatmapsTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_beatmap_backoff_does_not_fallback_to_mirrors(self) -> None:
        with (
            patch.object(
                cheesegull_beatmaps.osu_api_v2,
                "get_beatmap",
                AsyncMock(side_effect=OsuApiBackoffError),
            ),
            patch.object(
                cheesegull_beatmaps.osu_mirrors,
                "fetch_one_cheesegull_beatmap",
                AsyncMock(),
            ) as mirror_fetch,
        ):
            result = await cheesegull_beatmaps.fetch_one_cheesegull_beatmap(
                1,
                client_ip_address=None,
                client_user_agent=None,
            )

        self.assertIsNone(result)
        mirror_fetch.assert_not_awaited()

    async def test_beatmapset_backoff_does_not_fallback_to_mirrors(self) -> None:
        with (
            patch.object(
                cheesegull_beatmaps.osu_api_v2,
                "get_beatmapset",
                AsyncMock(side_effect=OsuApiBackoffError),
            ),
            patch.object(
                cheesegull_beatmaps.osu_mirrors,
                "fetch_one_cheesegull_beatmapset",
                AsyncMock(),
            ) as mirror_fetch,
        ):
            result = await cheesegull_beatmaps.fetch_one_cheesegull_beatmapset(
                1,
                client_ip_address=None,
                client_user_agent=None,
            )

        self.assertIsNone(result)
        mirror_fetch.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
