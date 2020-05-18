from sanic import Sanic
from sanic_test import TestManager
from sanic_test.testing import SanicASGITestClient, SanicTestClient


def test_legacy_support_initialization(app):
    assert isinstance(app.test_client, SanicTestClient)
    assert isinstance(app.asgi_client, SanicASGITestClient)


def test_manager_initialization(manager):
    assert isinstance(manager.test_client, SanicTestClient)
    assert isinstance(manager.asgi_client, SanicASGITestClient)
    assert isinstance(manager, TestManager)
