import pytest
from sanic import Sanic, response

from sanic_testing.reusable import ReusableClient


@pytest.fixture
def reusable_app():
    sanic_app = Sanic(__name__)

    @sanic_app.get("/")
    def basic(request):
        return response.text("foo")

    return sanic_app


@pytest.mark.asyncio
def test_basic_asgi_client(reusable_app):
    client = ReusableClient(reusable_app)
    with client:
        request, response = client.get("/")

        assert request.method.lower() == "get"
        assert response.body == b"foo"
        assert response.status == 200
