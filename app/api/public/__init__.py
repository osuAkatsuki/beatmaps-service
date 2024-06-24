from fastapi import APIRouter

from . import cheesegull

public_router = APIRouter()

public_router.include_router(cheesegull.router)
