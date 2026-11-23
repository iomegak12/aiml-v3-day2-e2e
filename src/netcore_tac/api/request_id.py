"""Give every HTTP request a UUID4 request ID (request.state + X-Request-ID header)."""

import uuid
from collections.abc import Callable

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

REQUEST_ID_HEADER = "X-Request-ID"


def new_request_id() -> str:
    """A fresh UUID4 string."""
    return str(uuid.uuid4())


class RequestIdMiddleware:
    """Pure ASGI middleware: sets ``scope["state"]["request_id"]`` and the response header."""

    def __init__(self, app: ASGIApp, id_factory: Callable[[], str] = new_request_id) -> None:
        self.app = app
        self.id_factory = id_factory

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = self.id_factory()
        scope.setdefault("state", {})["request_id"] = request_id

        async def send_with_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = request_id
            await send(message)

        await self.app(scope, receive, send_with_id)
