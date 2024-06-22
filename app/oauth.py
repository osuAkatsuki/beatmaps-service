from collections.abc import AsyncGenerator
from collections.abc import Generator
from typing import Any

import httpx


class AsyncOAuth(httpx.Auth):
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_endpoint: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_endpoint = token_endpoint

        self.access_token: str | None = None

        super().__init__(*args, **kwargs)

    def build_refresh_request(self) -> httpx.Request:
        return httpx.Request(
            "POST",
            self.token_endpoint,
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
                "scope": "public",
            },
        )

    def update_tokens(self, response: httpx.Response) -> None:
        response.raise_for_status()
        data = response.json()
        self.access_token = data["access_token"]

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

        if self.access_token is None:
            refresh_response = yield self.build_refresh_request()
            await refresh_response.aread()
            self.update_tokens(refresh_response)

        request.headers["Authorization"] = f"Bearer {self.access_token}"
        response = yield request

        while response.status_code == 401:
            refresh_response = yield self.build_refresh_request()
            await refresh_response.aread()
            self.update_tokens(refresh_response)

            request.headers["Authorization"] = f"Bearer {self.access_token}"
            response = yield request
