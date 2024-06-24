from fastapi import APIRouter

from .v1 import v1_router

internal_router = APIRouter()

internal_router.include_router(v1_router)
