import datetime
import json
import typing

import fastapi.responses


class JSONEncoder(json.JSONEncoder):
    def default(self, o: typing.Any) -> typing.Any:
        if isinstance(o, datetime.datetime):
            tz_suffix = "Z" if o.tzinfo in (None, datetime.UTC) else "%z"
            year_str = o.strftime("%Y").zfill(4)
            return o.strftime(f"{year_str}-%m-%dT%H:%M:%S{tz_suffix}")

        return super().default(o)


class JSONResponse(fastapi.responses.JSONResponse):
    def render(self, content: typing.Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            cls=JSONEncoder,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")
