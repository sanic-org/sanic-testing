import pytest

from sanic import Sanic, response
from sanic.asgi import ASGIApp
from sanic_test import TestManager


@pytest.fixture
def app():
    sanic_app = Sanic(__name__)
    TestManager(sanic_app)

    @sanic_app.route("/", methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"])
    def basic(request):
        return response.text("foo")

    return sanic_app


@pytest.fixture
def manager():
    sanic_app = Sanic(__name__)
    return TestManager(sanic_app)
