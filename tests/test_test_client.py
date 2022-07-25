import asyncio

import pytest
from sanic import Sanic, Websocket
from sanic.request import Request
from websockets.client import WebSocketClientProtocol


@pytest.mark.parametrize(
    "method", ["get", "post", "patch", "put", "delete", "options"]
)
def test_basic_test_client(app, method):
    request, response = getattr(app.test_client, method)("/")

    assert isinstance(request, Request)
    assert response.body == b"foo"
    assert response.status == 200
    assert response.content_type == "text/plain; charset=utf-8"


def test_websocket_route_basic(app):
    ev = asyncio.Event()

    @app.websocket("/ws")
    async def handler(request, ws):
        assert request.scheme == "ws"
        assert ws.subprotocol is None
        ev.set()

    request, response = app.test_client.websocket("/ws")
    assert response.opened is True
    assert ev.is_set()


def test_websocket_route_queue(app: Sanic):
    async def client_mimic(websocket: WebSocketClientProtocol):
        await websocket.send("foo")
        await websocket.recv()

    @app.websocket("/ws")
    async def handler(request, ws: Websocket):
        while True:
            await ws.send("hello!")
            if not await ws.recv():
                break

    _, response = app.test_client.websocket("/ws", mimic=client_mimic)
    assert response.server_sent == ["hello!"]
    assert response.server_received == ["foo", ""]


def test_websocket_client_mimic_failed(app: Sanic):
    @app.websocket("/ws")
    async def handler(request, ws: Websocket):
        pass

    async def client_mimic(websocket: WebSocketClientProtocol):
        raise Exception("Should fails")

    with pytest.raises(Exception, match="Should fails"):
        app.test_client.websocket("/ws", mimic=client_mimic)


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
