import asyncio

import pytest
from sanic.request import Request


@pytest.mark.parametrize(
    "method", ["get", "post", "patch", "put", "delete", "options"]
)
def test_basic_test_client(app, method):
    request, response = getattr(app.test_client, method)("/")

    assert isinstance(request, Request)
    assert response.body == b"foo"
    assert response.status == 200
    assert response.content_type == "text/plain; charset=utf-8"


def test_websocket_route(app):
    ev = asyncio.Event()

    @app.websocket("/ws")
    async def handler(request, ws):
        assert request.scheme == "ws"
        assert ws.subprotocol is None
        ev.set()

    request, response = app.test_client.websocket("/ws")
    assert response.opened is True
    assert ev.is_set()
