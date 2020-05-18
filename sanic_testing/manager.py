from sanic import Sanic
from sanic_testing.testing import SanicASGITestClient, SanicTestClient


class TestManager:
    def __init__(self, app: Sanic) -> None:
        self.test_client = SanicTestClient(app)
        self.asgi_client = SanicASGITestClient(app)
        app._test_manager = self
