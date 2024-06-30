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

OSU_API_V1_API_KEYS_POOL = os.environ["OSU_API_V1_API_KEY"].split(",")

DB_USER = os.environ["DB_USER"]
DB_PASS = os.environ["DB_PASS"]
DB_HOST = os.environ["DB_HOST"]
DB_PORT = int(os.environ["DB_PORT"])
DB_NAME = os.environ["DB_NAME"]

DISCORD_BEATMAP_UPDATES_WEBHOOK_URL = os.environ["DISCORD_BEATMAP_UPDATES_WEBHOOK_URL"]
