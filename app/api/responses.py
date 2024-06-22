import datetime
import json
import typing

import fastapi.responses


class JSONEncoder(json.JSONEncoder):
    def default(self, o: typing.Any) -> typing.Any:
        if isinstance(o, datetime.datetime):
            # Append "Z" for utc
            tz_suffix = "Z" if o.tzinfo in (None, datetime.UTC) else "%z"
            return o.strftime("%Y-%m-%dT%H:%M:%S" + tz_suffix)

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
