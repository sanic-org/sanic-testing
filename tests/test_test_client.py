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


def test_listeners(app):
    listeners = []
    available = (
        "before_server_start",
        "after_server_start",
        "before_server_stop",
        "after_server_stop",
    )

    @app.before_server_start
    async def before_server_start(*_):
        listeners.append("before_server_start")

    @app.after_server_start
    async def after_server_start(*_):
        listeners.append("after_server_start")

    @app.before_server_stop
    async def before_server_stop(*_):
        listeners.append("before_server_stop")

    @app.after_server_stop
    async def after_server_stop(*_):
        listeners.append("after_server_stop")

    app.test_client.get("/")

    assert len(listeners) == 4
    assert all(x in listeners for x in available)
