import pickle

import pytest
from sanic import Sanic

from sanic_testing import TestManager
from sanic_testing.testing import SanicASGITestClient, SanicTestClient


def test_legacy_support_initialization(app):
    assert isinstance(app.test_client, SanicTestClient)
    assert isinstance(app.asgi_client, SanicASGITestClient)


def test_manager_initialization(manager):
    assert isinstance(manager.test_client, SanicTestClient)
    assert isinstance(manager.asgi_client, SanicASGITestClient)
    assert isinstance(manager, TestManager)


@pytest.mark.parametrize("protocol", [3, 4])
def test_pickle_app(protocol):
    app = Sanic("test_pickle_app")
    manager = TestManager(app)
    assert app._test_manager == manager
    my_dict = {"app": app}
    app.router.reset()
    app.signal_router.reset()
    my_pickled = pickle.dumps(my_dict, protocol=protocol)
    del my_dict
    del app
    del manager
    my_new_dict = pickle.loads(my_pickled)
    assert my_new_dict["app"]._test_manager
