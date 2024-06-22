from fastapi import FastAPI

from app.api import api_router


def init_api() -> FastAPI:
    app = FastAPI()

    app.include_router(api_router)

    return app


asgi_app = init_api()
