from fastapi import APIRouter

from . import osu_api_v2
from . import osz2_files

v1_router = APIRouter()

v1_router.include_router(osu_api_v2.router)
v1_router.include_router(osz2_files.router)
