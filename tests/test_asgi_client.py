import asyncio

import pytest
from sanic.request import Request


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method", ["get", "post", "patch", "put", "delete", "options"]
)
async def test_basic_asgi_client(app, method):
    request, response = await getattr(app.asgi_client, method)("/")

    assert isinstance(request, Request)
    assert response.body == b"foo"
    assert response.status == 200
    assert response.content_type == "text/plain; charset=utf-8"


@pytest.mark.asyncio
async def test_websocket_route(app):
    ev = asyncio.Event()

    @app.websocket("/ws")
    async def handler(request, ws):
        ev.set()

    await app.asgi_client.websocket("/ws")
    assert ev.is_set()


@pytest.mark.asyncio
async def test_listeners(app):
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

    await app.asgi_client.get("/")

    assert len(listeners) == 4
    assert all(x in listeners for x in available)
