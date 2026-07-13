from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from fastapi.responses import JSONResponse

from core.api.app import app as control_plane_app


ASGIScope = dict[str, Any]
ASGIReceive = Callable[[], Awaitable[dict[str, Any]]]
ASGISend = Callable[[dict[str, Any]], Awaitable[None]]

READ_ONLY_METHODS = {
    "GET",
    "HEAD",
    "OPTIONS",
}


class ReadOnlyASGI:
    def __init__(self, application: Any) -> None:
        self.application = application

    async def __call__(
        self,
        scope: ASGIScope,
        receive: ASGIReceive,
        send: ASGISend,
    ) -> None:
        if (
            scope.get("type") == "http"
            and scope.get("method", "").upper()
            not in READ_ONLY_METHODS
        ):
            response = JSONResponse(
                status_code=405,
                content={
                    "detail": "shadow_read_only",
                    "mode": "shadow-read-only",
                    "allowed_methods": sorted(
                        READ_ONLY_METHODS
                    ),
                },
            )

            await response(
                scope,
                receive,
                send,
            )
            return

        await self.application(
            scope,
            receive,
            send,
        )


app = ReadOnlyASGI(control_plane_app)
