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
