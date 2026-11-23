"""Unit tests for netcore_tac.api.request_id."""

import asyncio
import uuid

from netcore_tac.api.request_id import RequestIdMiddleware, new_request_id


def test_new_request_id_is_uuid4():
    assert uuid.UUID(new_request_id()).version == 4
    assert new_request_id() != new_request_id()


def test_middleware_sets_state_and_header():
    seen = {}

    async def app(scope, receive, send):
        seen["state_id"] = scope["state"]["request_id"]
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    messages = []

    async def send(message):
        messages.append(message)

    scope = {"type": "http", "path": "/", "headers": []}
    asyncio.run(RequestIdMiddleware(app, id_factory=lambda: "fixed-id")(scope, None, send))

    headers = dict(messages[0]["headers"])
    assert headers[b"x-request-id"] == b"fixed-id"
    assert seen["state_id"] == "fixed-id"


def test_non_http_scope_passes_through():
    called = []

    async def app(scope, receive, send):
        called.append(scope["type"])

    asyncio.run(RequestIdMiddleware(app)({"type": "lifespan"}, None, None))
    assert called == ["lifespan"]
