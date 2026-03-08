from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel

from app import state


class MirrorResource(StrEnum):
    OSZ_FILE = "osz_file"
    BACKGROUND_IMAGE = "background_image"
    # TODO: beatmap audio file


class BeatmapMirrorRequest(BaseModel):
    request_url: str
    api_key_id: str | None
    mirror_name: str
    success: bool
    started_at: datetime
    ended_at: datetime
    response_status_code: int | None
    response_size: int
    response_error: str | None
    resource: MirrorResource


async def create(
    request_url: str,
    api_key_id: str | None,
    mirror_name: str,
    success: bool,
    started_at: datetime,
    ended_at: datetime,
    response_status_code: int | None,
    response_size: int,
    response_error: str | None,
    resource: MirrorResource,
) -> BeatmapMirrorRequest:
    query = """\
        INSERT INTO beatmap_mirror_requests (
            request_url, api_key_id, mirror_name, success, started_at,
            ended_at, response_status_code, response_size, response_error, resource
        )
        VALUES (
            :request_url, :api_key_id, :mirror_name, :success, :started_at,
            :ended_at, :response_status_code, :response_size, :response_error, :resource
        )
    """
    await state.database.execute(
        query=query,
        values={
            "request_url": request_url,
            "api_key_id": api_key_id,
            "mirror_name": mirror_name,
            "success": success,
            "started_at": started_at,
            "ended_at": ended_at,
            "response_status_code": response_status_code,
            "response_size": response_size,
            "response_error": response_error,
            "resource": resource.value,
        },
    )
    return BeatmapMirrorRequest(
        request_url=request_url,
        api_key_id=api_key_id,
        mirror_name=mirror_name,
        success=success,
        started_at=started_at,
        ended_at=ended_at,
        response_status_code=response_status_code,
        response_size=response_size,
        response_error=response_error,
        resource=resource,
    )
