import logging

from fastapi import FastAPI
from fastapi import Request
from fastapi import Response
from starlette.middleware.base import RequestResponseEndpoint

from app import settings
from app.api import api_router


def init_routes(app: FastAPI) -> FastAPI:
    app.include_router(api_router)
    return app


def init_middleware(app: FastAPI) -> FastAPI:
    @app.middleware("http")
    async def http_middleware(
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        try:
            return await call_next(request)
        except BaseException:
            logging.exception("Exception in ASGI application")
            return Response(status_code=500)

    return app


def init_api() -> FastAPI:
    app = FastAPI(
        docs_url="/docs" if settings.APP_ENV != "production" else None,
        redoc_url="/redoc" if settings.APP_ENV != "production" else None,
    )
    app = init_routes(app)
    app = init_middleware(app)
    return app


asgi_app = init_api()
