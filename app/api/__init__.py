from fastapi import APIRouter

from app.api.health import health_router
from app.api.internal import internal_router
from app.api.public import public_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(internal_router)
api_router.include_router(public_router)
