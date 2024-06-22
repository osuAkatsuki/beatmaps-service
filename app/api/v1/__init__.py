from fastapi import APIRouter

from . import cheesegull

v1_router = APIRouter()


v1_router.include_router(cheesegull.router)
