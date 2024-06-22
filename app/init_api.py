import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from databases import Database
from fastapi import FastAPI
from fastapi import Request
from fastapi import Response
from starlette.middleware.base import RequestResponseEndpoint

from app import settings
from app import state
from app.adapters import mysql
from app.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await state.database.connect()
    yield
    await state.database.disconnect()


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


def init_db(app: FastAPI) -> FastAPI:
    state.database = Database(
        url=mysql.create_dsn(
            driver="aiomysql",
            username=settings.DB_USER,
            password=settings.DB_PASS,
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
        ),
    )
    return app


def init_api() -> FastAPI:
    app = FastAPI(
        openapi_url="/openapi.json" if settings.APP_ENV != "production" else None,
        docs_url="/docs" if settings.APP_ENV != "production" else None,
        redoc_url="/redoc" if settings.APP_ENV != "production" else None,
        swagger_ui_oauth2_redirect_url=None,
        lifespan=lifespan,
    )
    app = init_routes(app)
    app = init_middleware(app)
    app = init_db(app)
    return app


asgi_app = init_api()
