from fastapi import FastAPI

from app.api.v1 import v1_router


def init_api() -> FastAPI:
    app = FastAPI()

    app.include_router(v1_router)

    return app


asgi_app = init_api()
