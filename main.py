#!/usr/bin/env python3
import uvicorn

from app import settings


def main() -> int:
    uvicorn.run(
        "app.init_api:asgi_app",
        reload=settings.CODE_HOTRELOAD,
        server_header=False,
        date_header=False,
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        access_log=False,
    )
    return 0


if __name__ == "__main__":
    exit(main())
