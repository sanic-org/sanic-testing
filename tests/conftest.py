import pytest

from sanic import Sanic, response
from sanic.asgi import ASGIApp
from sanic_test import TestManager

# # async def asgi_app(scope, receive, send):


# class DummySanic:
#     async def __call__(self, scope, receive, send):
#         asgi_app = await ASGIApp.create(self, scope, receive, send)
#         await asgi_app()


# class ASGIApp:
#     def __init__(self, sanic_app, scope):
#         self.sanic_app = sanic_app
#         self.scope = scope
#         url_bytes = scope.get("root_path", "") + scope["path"]
#         url_bytes = url_bytes.encode("latin-1")
#         url_bytes += scope["query_string"]
#         # headers = CIMultiDict(
#         #     [
#         #         (key.decode("latin-1"), value.decode("latin-1"))
#         #         for key, value in scope.get("headers", [])
#         #     ]
#         # )
#         # version = scope["http_version"]
#         # method = scope["method"]
#         # self.request = Request(
#         #     url_bytes, headers, version, method, MockTransport(scope)
#         # )
#         # self.request.app = sanic_app

#     async def read_body(self, receive):
#         pass

#     async def __call__(self, receive, send):
#         incoming = await receive()
#         print("\n\n>>>> REQUEST")
#         print(f"scope: {self.scope}")
#         print(f"incoming: {incoming}\n\n")
#         await send(
#             {
#                 "type": "http.response.start",
#                 "status": 200,
#                 "headers": [[b"content-type", b"text/plain"]],
#             }
#         )
#         await send({"type": "http.response.body", "body": b"123"})

#     async def stream_callback(self, response):
#         pass


@pytest.fixture
def app():
    sanic_app = Sanic(__name__)
    TestManager(sanic_app)

    @sanic_app.get("/")
    def basic(request):
        return response.text("foo")

    return sanic_app


@pytest.fixture
def manager():
    sanic_app = Sanic(__name__)
    return TestManager(sanic_app)
