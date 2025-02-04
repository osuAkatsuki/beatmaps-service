import logging
import random
from collections.abc import AsyncGenerator
from collections.abc import Generator
from typing import Any

import httpx
from pydantic import BaseModel


class OAuthClientCredentials(BaseModel):
    client_id: str
    client_secret: str

    access_token: str | None = None


class AsyncOAuth(httpx.Auth):
    def __init__(
        self,
        client_credential_sets: list[OAuthClientCredentials],
        token_endpoint: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.client_credential_sets = client_credential_sets
        self.token_endpoint = token_endpoint

        super().__init__(*args, **kwargs)

    def build_refresh_request(
        self,
        client_credentials: OAuthClientCredentials,
    ) -> httpx.Request:
        return httpx.Request(
            "POST",
            self.token_endpoint,
            data={
                "client_id": client_credentials.client_id,
                "client_secret": client_credentials.client_secret,
                "grant_type": "client_credentials",
                "scope": "public",
            },
        )

    def sync_auth_flow(
        self,
        request: httpx.Request,
    ) -> Generator[httpx.Request, httpx.Response, None]:
        raise RuntimeError(
            "Cannot use a sync authentication class with httpx.AsyncClient",
        )

    async def async_auth_flow(
        self,
        request: httpx.Request,
    ) -> AsyncGenerator[httpx.Request, httpx.Response]:
        if self.requires_request_body:
            await request.aread()

        client_credentials = random.choice(self.client_credential_sets)

        if client_credentials.access_token is None:
            refresh_response = yield self.build_refresh_request(client_credentials)
            await refresh_response.aread()
            refresh_response_data = refresh_response.json()
            if "access_token" not in refresh_response_data:
                logging.warning(
                    "Failed to get oauth access token",
                    extra={"response_data": refresh_response_data},
                )
            client_credentials.access_token = refresh_response_data["access_token"]

        request.headers["Authorization"] = f"Bearer {client_credentials.access_token}"
        response = yield request

        while response.status_code == 401:
            refresh_response = yield self.build_refresh_request(client_credentials)
            await refresh_response.aread()
            refresh_response_data = refresh_response.json()
            if "access_token" not in refresh_response_data:
                logging.warning(
                    "Failed to get oauth access token",
                    extra={"response_data": refresh_response_data},
                )
            client_credentials.access_token = refresh_response_data["access_token"]

            request.headers["Authorization"] = (
                f"Bearer {client_credentials.access_token}"
            )
            response = yield request

        # TODO: refactor this log to work with osu api v1, be more specific etc.
        logging.info(
            "Made oauth-authorized request",
            extra={
                "request_url": request.url._uri_reference._asdict(),
                "ratelimit": {
                    "remaining": response.headers.get("X-Ratelimit-Remaining"),
                    "limit": response.headers.get("X-Ratelimit-Limit"),
                    "reset_utc": response.headers.get("X-Ratelimit-Reset"),
                },
                "client_credentials": {"client_id": client_credentials.client_id},
            },
        )
