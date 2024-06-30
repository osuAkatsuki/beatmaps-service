from fastapi import APIRouter

from . import akatsuki
from . import osu_api_v2

v1_router = APIRouter()

v1_router.include_router(akatsuki.router)
v1_router.include_router(osu_api_v2.router)
