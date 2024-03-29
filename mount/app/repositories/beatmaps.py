from __future__ import annotations

import datetime
from typing import Any

from app.common import services
from app.common import settings


# TODO: typeddict model for mapping?
id_cache: dict[int, dict[str, Any]] = {}


async def get_from_id(id: int) -> dict[str, Any] | None:
    """\
    Fetch a beatmap's metadata from it's id.

    https://github.com/ppy/osu-api/wiki#apiget_beatmaps
    """

    # fetch the beatmap from ram if possible
    if beatmap_data := id_cache.get(id):
        return beatmap_data

    # fetch the beatmap from elasticsearch if possible
    if await services.elastic_client.exists(
        index=settings.BEATMAPS_INDEX,
        id=str(id),
    ):
        response = await services.elastic_client.get_source(
            index=settings.BEATMAPS_INDEX,
            id=str(id),
        )

        # we found the map from elasticsearch
        beatmap_data = response.body["data"]
    else:
        try:
            beatmap_data = await services.osu_api_client.get_beatmap(id)
        except services.OsuAPIRequestError as exc:
            if exc.status_code == 404:
                return None
            else:
                raise
        else:
            # save the beatmap into our elasticsearch index
            await services.elastic_client.create(
                index=settings.BEATMAPS_INDEX,
                id=str(id),
                document={
                    "data": beatmap_data,
                    "created_at": datetime.datetime.now().isoformat(),
                    "updated_at": datetime.datetime.now().isoformat(),
                },
            )

    # cache the beatmap in ram
    # id_cache[id] = beatmap_data

    return beatmap_data


async def get_from_checksum(checksum: str) -> dict[str, Any] | None:
    """Get a beatmap from it's md5 checksum."""
    ...
