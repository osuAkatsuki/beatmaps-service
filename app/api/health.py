from fastapi import APIRouter
from fastapi import Response

health_router = APIRouter(tags=["Service Health API"])


@health_router.get("/_health")
async def healthcheck() -> Response:
    return Response(status_code=200)
