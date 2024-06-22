from fastapi import APIRouter

from . import cheesegull
from . import osz2_files

v1_router = APIRouter()

v1_router.include_router(cheesegull.router)
v1_router.include_router(osz2_files.router)
