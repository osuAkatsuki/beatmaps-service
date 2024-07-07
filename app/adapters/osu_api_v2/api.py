import logging
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


osu_api_v2_http_client = httpx.AsyncClient(
    base_url="https://osu.ppy.sh/api/v2/",
    auth=oauth.AsyncOAuth(
        client_credential_sets=[
            oauth.OAuthClientCredentials(
                client_id=settings.OSU_API_V2_CLIENT_ID,
                client_secret=settings.OSU_API_V2_CLIENT_SECRET,
            ),
        ],
        token_endpoint=OSU_API_V2_TOKEN_ENDPOINT,
    ),
    timeout=httpx.Timeout(15),
)


async def get_beatmap(beatmap_id: int) -> BeatmapExtended | None:
    osu_api_response_data: dict[str, Any] | None = None
    try:
        response = await osu_api_v2_http_client.get(f"beatmaps/{beatmap_id}")
        if response.status_code in (404, 451):
            return None
        response.raise_for_status()
        osu_api_response_data = response.json()
        assert osu_api_response_data is not None
        return BeatmapExtended(**osu_api_response_data)
    except Exception:
        logging.exception(
            "Failed to fetch beatmap from osu! API v2",
            extra={
                "beatmap_id": beatmap_id,
                "osu_api_response_data": osu_api_response_data,
            },
        )
        raise


async def get_beatmapset(beatmapset_id: int) -> BeatmapsetExtended | None:
    osu_api_response_data: dict[str, Any] | None = None
    try:
        response = await osu_api_v2_http_client.get(f"beatmapsets/{beatmapset_id}")
        if response.status_code in (404, 451):
            return None
        response.raise_for_status()
        osu_api_response_data = response.json()
        assert osu_api_response_data is not None
        return BeatmapsetExtended(**osu_api_response_data)
    except Exception:
        logging.exception(
            "Failed to fetch beatmapset from osu! API v2",
            extra={
                "beatmapset_id": beatmapset_id,
                "osu_api_response_data": osu_api_response_data,
            },
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
            "Failed to fetch beatmapsets from osu! API v2",
            extra={
                "query": query,
                "general_settings": (
                    {s.name for s in general_settings}
                    if general_settings is not None
                    else None
                ),
                "extras": {s.name for s in extras} if extras is not None else None,
                "mode": mode.name if mode is not None else None,
                "category": category.name if category is not None else None,
                "filter_nsfw": filter_nsfw,
                "language_id": language_id.value if language_id is not None else None,
                "genre_id": genre_id.value if genre_id is not None else None,
                "sort_by": sort_by.name if sort_by else None,
                "page": page,
                "cursor_string": cursor_string,
                "osu_api_response_data": osu_api_response_data,
            },
        )
        raise
