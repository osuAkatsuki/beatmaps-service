import os
import unittest

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

from app.adapters import osu_mirrors
from app.repositories.beatmap_mirror_requests import MirrorResource


class OsuMirrorsTestCase(unittest.TestCase):
    def test_cheesegull_beatmap_metadata_uses_only_supporting_mirrors(self) -> None:
        mirrors = osu_mirrors.get_available_mirrors(MirrorResource.CHEESEGULL_BEATMAP)

        self.assertEqual([mirror.name for mirror in mirrors], ["osu_direct"])

    def test_cheesegull_beatmapset_metadata_uses_only_supporting_mirrors(self) -> None:
        mirrors = osu_mirrors.get_available_mirrors(
            MirrorResource.CHEESEGULL_BEATMAPSET,
        )

        self.assertEqual([mirror.name for mirror in mirrors], ["osu_direct"])


if __name__ == "__main__":
    unittest.main()
