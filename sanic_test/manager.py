from sanic import Sanic
from sanic_test.testing import SanicASGITestClient, SanicTestClient


class TestManager:
    def __init__(self, app: Sanic) -> None:
        self.test_client = SanicTestClient(app)
        self.asgi_client = SanicASGITestClient(app)

        app.test_client = self.test_client
        app.asgi_client = self.asgi_client
