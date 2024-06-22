import logging
from datetime import datetime
from datetime import timezone
from typing import Any

import httpx

from app import oauth
from app import settings
from app.adapters.osu_api_v2.models import BeatmapExtended
from app.adapters.osu_api_v2.models import BeatmapsetExtended
from app.adapters.osu_api_v2.models import BeatmapsetSearchResponse
from app.adapters.osu_api_v2.models import Category
from app.adapters.osu_api_v2.models import Extra
from app.adapters.osu_api_v2.models import GeneralSetting
from app.adapters.osu_api_v2.models import GenreId
from app.adapters.osu_api_v2.models import LanguageId
from app.adapters.osu_api_v2.models import SortBy
from app.common_models import GameMode

OSU_API_V2_TOKEN_ENDPOINT = "https://osu.ppy.sh/oauth/token"


async def log_osu_api_response(response: httpx.Response) -> None:
    if response.request.url == OSU_API_V2_TOKEN_ENDPOINT or response.status_code == 401:
        return None

    # TODO: Migrate to or add statsd metric to count overall number of
    #       authorized requests to the osu! api, so we can understand
    #       our overall request count and frequency.
    logging.info(
        "Made authorized request to osu! api",
        extra={
            "request_url": response.request.url,
            "ratelimit": {
                "remaining": response.headers.get("X-Ratelimit-Remaining"),
                "limit": response.headers.get("X-Ratelimit-Limit"),
                "reset_utc": (
                    # they don't send a header, but reset on the minute
                    datetime.now(tz=timezone.utc)
                    .replace(second=0, microsecond=0)
                    .isoformat()
                ),
            },
        },
    )
    return None


osu_api_v2_http_client = httpx.AsyncClient(
    base_url="https://osu.ppy.sh/api/v2/",
    auth=oauth.AsyncOAuth(
        client_id=settings.OSU_API_V2_CLIENT_ID,
        client_secret=settings.OSU_API_V2_CLIENT_SECRET,
        token_endpoint=OSU_API_V2_TOKEN_ENDPOINT,
    ),
    event_hooks={"response": [log_osu_api_response]},
    timeout=5.0,
)


async def get_beatmap(beatmap_id: int) -> BeatmapExtended | None:
    osu_api_response_data: dict[str, Any] | None = None
    try:
        response = await osu_api_v2_http_client.get(f"beatmaps/{beatmap_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        osu_api_response_data = response.json()
        assert osu_api_response_data is not None
        return BeatmapExtended(**osu_api_response_data)
    except Exception:
        logging.exception(
            "Failed to fetch beatmap from osu! API",
            extra={"osu_api_response_data": osu_api_response_data},
        )
        raise


async def get_beatmapset(beatmapset_id: int) -> BeatmapsetExtended | None:
    osu_api_response_data: dict[str, Any] | None = None
    try:
        response = await osu_api_v2_http_client.get(f"beatmapsets/{beatmapset_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        osu_api_response_data = response.json()
        assert osu_api_response_data is not None
        return BeatmapsetExtended(**osu_api_response_data)
    except Exception:
        logging.exception(
            "Failed to fetch beatmapset from osu! API",
            extra={"osu_api_response_data": osu_api_response_data},
        )
        raise


async def search_beatmapsets(
    query: str,
    *,
    general_settings: set[GeneralSetting] | None = None,
    extras: set[Extra] | None = None,
    mode: GameMode | None = None,
    category: Category | None = None,
    filter_nsfw: bool = True,
    language_id: LanguageId | None = None,
    genre_id: GenreId | None = None,
    sort_by: SortBy | None = None,
    page: int | None = None,
    cursor_string: str | None = None,
) -> BeatmapsetSearchResponse:
    if [page, cursor_string].count(None) != 1:
        raise ValueError("Exactly one of page or cursor_string must be provided")

    osu_api_response_data: dict[str, Any] | None = None
    try:
        response = await osu_api_v2_http_client.get(
            "beatmapsets/search",
            params={
                "e": ".".join(extras) if extras else "",
                "c": ".".join(general_settings) if general_settings else "",
                "g": genre_id.value if genre_id else "",
                "l": language_id.value if language_id else "",
                "m": mode,
                "nsfw": "" if filter_nsfw else "false",
                "played": "",
                "q": query,
                "sort": sort_by.value if sort_by else "",
                "s": category,
                **({"page": page} if page else {}),
                **({"cursor_string": cursor_string} if cursor_string else {}),
            },
        )
        response.raise_for_status()
        osu_api_response_data = response.json()
        assert osu_api_response_data is not None
        return BeatmapsetSearchResponse(**osu_api_response_data)
    except Exception:
        logging.exception(
            "Failed to fetch beatmapsets from osu! API",
            extra={"osu_api_response_data": osu_api_response_data},
        )
        raise
