from fastapi import APIRouter

from . import cheesegull
from . import osz2_files

public_router = APIRouter()

public_router.include_router(cheesegull.router)
public_router.include_router(osz2_files.router)
