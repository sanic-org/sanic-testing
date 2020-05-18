import pytest

from sanic.request import Request


@pytest.mark.asyncio
async def test_basic_asgi_client(app):
    for method in ['get', "post", "patch", "put", "delete", "options"]:
        request, response = await getattr(app.asgi_client, method)("/")

        assert isinstance(request, Request)
        assert response.body == b"foo"
        assert response.status == 200
        assert response.content_type == "text/plain; charset=utf-8"


@pytest.mark.asyncio
async def test_websocket_route(app):

    @app.websocket("/ws")
    async def handler(request, ws):
        ...

    with pytest.raises(Exception):
        await app.asgi_client.websocket("/ws")
