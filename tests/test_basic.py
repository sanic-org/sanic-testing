from sanic import Sanic
from sanic_test import TestManager
from sanic_test.testing import SanicASGITestClient, SanicTestClient

# from requests_async import ASGISession
# import pytest


# @pytest.mark.asyncio
# async def test_basic_connection(app):
#     client = ASGISession(app)
#     response = await client.get("/")
#     assert response.status_code == 200
#     assert response.text == "123"


def test_legacy_support_initialization(app):
    assert isinstance(app.test_client, SanicTestClient)
    assert isinstance(app.asgi_client, SanicASGITestClient)


def test_manager_initialization(manager):
    assert isinstance(manager.test_client, SanicTestClient)
    assert isinstance(manager.asgi_client, SanicASGITestClient)
    assert isinstance(manager, TestManager)
