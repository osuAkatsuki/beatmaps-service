# This portion is based off cmyui's discord hooks code
# https://github.com/cmyui/cmyui_pkg/blob/master/cmyui/discord/webhook.py
import logging
from typing import TYPE_CHECKING
from typing import Any
from typing import Literal

import httpx

from app import job_scheduling
from app import settings

if TYPE_CHECKING:
    from app.repositories.akatsuki_beatmaps import AkatsukiBeatmap

discord_webhooks_http_client = httpx.AsyncClient()


EDIT_COL = "4360181"
EDIT_ICON = "https://cdn3.iconfinder.com/data/icons/bold-blue-glyphs-free-samples/32/Info_Circle_Symbol_Information_Letter-512.png"


class Footer:
    def __init__(self, text: str, **kwargs: Any) -> None:
        self.text = text
        self.icon_url = kwargs.get("icon_url")
        self.proxy_icon_url = kwargs.get("proxy_icon_url")


class Image:
    def __init__(self, **kwargs: Any) -> None:
        self.url = kwargs.get("url")
        self.proxy_url = kwargs.get("proxy_url")
        self.height = kwargs.get("height")
        self.width = kwargs.get("width")


class Thumbnail:
    def __init__(self, **kwargs: Any) -> None:
        self.url = kwargs.get("url")
        self.proxy_url = kwargs.get("proxy_url")
        self.height = kwargs.get("height")
        self.width = kwargs.get("width")


class Video:
    def __init__(self, **kwargs: Any) -> None:
        self.url = kwargs.get("url")
        self.height = kwargs.get("height")
        self.width = kwargs.get("width")


class Provider:
    def __init__(self, **kwargs: Any) -> None:
        self.url = kwargs.get("url")
        self.name = kwargs.get("name")


class Author:
    def __init__(self, **kwargs: Any) -> None:
        self.name = kwargs.get("name")
        self.url = kwargs.get("url")
        self.icon_url = kwargs.get("icon_url")
        self.proxy_icon_url = kwargs.get("proxy_icon_url")


class Field:
    def __init__(self, name: str, value: str, inline: bool = False) -> None:
        self.name = name
        self.value = value
        self.inline = inline


class Embed:
    def __init__(self, **kwargs: Any) -> None:
        self.title = kwargs.get("title")
        self.type = kwargs.get("type")
        self.description = kwargs.get("description")
        self.url = kwargs.get("url")
        self.timestamp = kwargs.get("timestamp")  # datetime
        self.color = kwargs.get("color", 0x000000)

        self.footer: Footer | None = kwargs.get("footer")
        self.image: Image | None = kwargs.get("image")
        self.thumbnail: Thumbnail | None = kwargs.get("thumbnail")
        self.video: Video | None = kwargs.get("video")
        self.provider: Provider | None = kwargs.get("provider")
        self.author: Author | None = kwargs.get("author")

        self.fields: list[Field] = kwargs.get("fields", [])

    def set_footer(self, **kwargs: Any) -> None:
        self.footer = Footer(**kwargs)

    def set_image(self, **kwargs: Any) -> None:
        self.image = Image(**kwargs)

    def set_thumbnail(self, **kwargs: Any) -> None:
        self.thumbnail = Thumbnail(**kwargs)

    def set_video(self, **kwargs: Any) -> None:
        self.video = Video(**kwargs)

    def set_provider(self, **kwargs: Any) -> None:
        self.provider = Provider(**kwargs)

    def set_author(self, **kwargs: Any) -> None:
        self.author = Author(**kwargs)

    def add_field(self, name: str, value: str, inline: bool = False) -> None:
        self.fields.append(Field(name, value, inline))


class Webhook:
    """A class to represent a single-use Discord webhook."""

    __slots__ = ("url", "content", "username", "avatar_url", "tts", "file", "embeds")

    def __init__(self, url: str, **kwargs: Any) -> None:
        self.url = url
        self.content = kwargs.get("content")
        self.username = kwargs.get("username")
        self.avatar_url = kwargs.get("avatar_url")
        self.tts = kwargs.get("tts")
        self.file = kwargs.get("file")
        self.embeds: list[Embed] = kwargs.get("embeds", [])

    def add_embed(self, embed: Embed) -> None:
        self.embeds.append(embed)

    @property
    def json(self) -> dict[str, Any]:
        if not any([self.content, self.file, self.embeds]):
            raise Exception(
                "Webhook must contain atleast one " "of (content, file, embeds).",
            )

        if self.content and len(self.content) > 2000:
            raise Exception("Webhook content must be under " "2000 characters.")

        payload: dict[str, Any] = {"embeds": []}

        for key in ("content", "username", "avatar_url", "tts", "file"):
            if (val := getattr(self, key)) is not None:
                payload[key] = val

        for embed in self.embeds:
            embed_payload = {}

            # simple params
            for key in ("title", "type", "description", "url", "timestamp", "color"):
                if val := getattr(embed, key):
                    embed_payload[key] = val

            # class params, must turn into dict
            for key in ("footer", "image", "thumbnail", "video", "provider", "author"):
                if val := getattr(embed, key):
                    embed_payload[key] = val.__dict__

            if embed.fields:
                embed_payload["fields"] = [f.__dict__ for f in embed.fields]

            payload["embeds"].append(embed_payload)

        return payload

    async def post(self) -> None:
        """Post the webhook in JSON format."""
        response = await discord_webhooks_http_client.post(
            self.url,
            json=self.json,
        )
        response.raise_for_status()


async def wrap_hook(webhook_url: str, embed: Embed) -> None:
    """Handles sending the webhook to discord."""

    logging.info("Sending Discord webhook")

    try:
        wh = Webhook(webhook_url, tts=False, username="LESS Score Server")
        wh.add_embed(embed)
        await wh.post()
    except Exception:
        logging.exception(
            "Failed to send Discord webhook",
            extra={"embed": embed},
        )


def schedule_hook(*, webhook_url: str | None, embed: Embed) -> None:
    """Performs a hook execution in a non-blocking manner."""

    if not webhook_url:
        return None

    job_scheduling.schedule_job(wrap_hook(webhook_url, embed))

    logging.debug("Scheduled the performing of a discord webhook!")
    return None


def beatmap_status_change(
    *,
    old_beatmap: "AkatsukiBeatmap",
    new_beatmap: "AkatsukiBeatmap",
    action_taken: Literal["status_change", "frozen"],
) -> None:
    embed = Embed(title="Beatmap Status/Freeze Change During Update!", color=EDIT_COL)
    if action_taken == "status_change":
        embed.description = f"Non-frozen {old_beatmap.embed} has just been changed from {old_beatmap.ranked.name} to {new_beatmap.ranked.name}!"
    else:
        embed.description = f"{new_beatmap.embed} has just been frozen in transit from {old_beatmap.ranked.name} to {new_beatmap.ranked.name}!"
    embed.set_author(name="beatmaps-service", icon_url=EDIT_ICON)
    embed.set_footer(text="This is an automated action performed by the server.")

    schedule_hook(
        webhook_url=settings.DISCORD_BEATMAP_UPDATES_WEBHOOK_URL,
        embed=embed,
    )
