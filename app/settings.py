import os

from dotenv import load_dotenv

load_dotenv()


def read_bool(s: str) -> bool:
    return s.lower() == "true"


APP_ENV = os.environ["APP_ENV"]
APP_HOST = os.environ["APP_HOST"]
APP_PORT = int(os.environ["APP_PORT"])

CODE_HOTRELOAD = read_bool(os.environ["CODE_HOTRELOAD"])

OSU_API_V2_CLIENT_ID = os.environ["OSU_API_V2_CLIENT_ID"]
OSU_API_V2_CLIENT_SECRET = os.environ["OSU_API_V2_CLIENT_SECRET"]

OSU_API_V1_API_KEYS_POOL = os.environ["OSU_API_V1_API_KEYS_POOL"].split(",")

DB_USER = os.environ["DB_USER"]
DB_PASS = os.environ["DB_PASS"]
DB_HOST = os.environ["DB_HOST"]
DB_PORT = int(os.environ["DB_PORT"])
DB_NAME = os.environ["DB_NAME"]

AWS_S3_ENDPOINT_URL = os.environ["AWS_S3_ENDPOINT_URL"]
AWS_S3_REGION_NAME = os.environ["AWS_S3_REGION_NAME"]
AWS_S3_BUCKET_NAME = os.environ["AWS_S3_BUCKET_NAME"]
AWS_S3_ACCESS_KEY_ID = os.environ["AWS_S3_ACCESS_KEY_ID"]
AWS_S3_SECRET_ACCESS_KEY = os.environ["AWS_S3_SECRET_ACCESS_KEY"]

DISCORD_BEATMAP_UPDATES_WEBHOOK_URL = os.environ["DISCORD_BEATMAP_UPDATES_WEBHOOK_URL"]

MINO_INCREASED_RATELIMIT_KEY = os.environ["MINO_INCREASED_RATELIMIT_KEY"]
