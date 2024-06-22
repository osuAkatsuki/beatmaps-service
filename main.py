#!/usr/bin/env python3
from fastapi import FastAPI

from app.api.v1 import v1_router

app = FastAPI()

app.include_router(v1_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app")
