import pytest
from sanic import Sanic, response

from sanic_testing import TestManager


def _basic_response(request):
    return response.text("foo")


@pytest.fixture
def app():
    sanic_app = Sanic(__name__)
    TestManager(sanic_app)

    sanic_app.route(
        "/", methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"]
    )(_basic_response)
    return sanic_app


@pytest.fixture
def manager():
    sanic_app = Sanic(__name__)
    return TestManager(sanic_app)
