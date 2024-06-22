import datetime
import json
import typing

import fastapi.responses


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()
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
