import asyncio
import typing
from asyncio.events import get_event_loop
from json import JSONDecodeError
from socket import socket
from types import SimpleNamespace

import httpx
import websockets
from sanic import Sanic
from sanic.asgi import ASGIApp
from sanic.exceptions import MethodNotSupported
from sanic.log import logger
from sanic.request import Request
from sanic.response import HTTPResponse, text

ASGI_HOST = "mockserver"
ASGI_PORT = 1234
ASGI_BASE_URL = f"http://{ASGI_HOST}:{ASGI_PORT}"
HOST = "127.0.0.1"
PORT = None

Sanic.test_mode = True


class SanicTestClient:
    def __init__(
        self, app: Sanic, port: typing.Optional[int] = PORT, host: str = HOST
    ) -> None:
        """Use port=None to bind to a random port"""
        self.app = app
        self.port = port
        self.host = host

        @app.listener("after_server_start")
        def _start_test_mode(sanic, *args, **kwargs):
            sanic.test_mode = True

        @app.listener("before_server_end")
        def _end_test_mode(sanic, *args, **kwargs):
            sanic.test_mode = False

    def get_new_session(self, **kwargs) -> httpx.AsyncClient:
        return httpx.AsyncClient(verify=False, **kwargs)

    async def _local_request(self, method: str, url: str, *args, **kwargs):
        logger.info(url)
        raw_cookies = kwargs.pop("raw_cookies", None)
        session_kwargs = kwargs.pop("session_kwargs", {})

        if method == "websocket":
            ws_proxy = SimpleNamespace()
            async with websockets.connect(url, *args, **kwargs) as websocket:
                ws_proxy.ws = websocket
                ws_proxy.opened = True
            return ws_proxy
        else:
            async with self.get_new_session(**session_kwargs) as session:

                try:
                    if method == "request":
                        args = [url] + list(args)
                        url = kwargs.pop("http_method", "GET").upper()
                    response = await getattr(session, method.lower())(
                        url, *args, **kwargs
                    )
                except httpx.HTTPError as e:
                    if hasattr(e, "response"):
                        response = e.response
                    else:
                        logger.error(
                            f"{method.upper()} {url} received no response!",
                            exc_info=True,
                        )
                        return None

                response.body = await response.aread()
                response.status = response.status_code
                response.content_type = response.headers.get("content-type")

                # response can be decoded as json after response._content
                # is set by response.aread()
                try:
                    response.json = response.json()
                except (JSONDecodeError, UnicodeDecodeError):
                    response.json = None

                if raw_cookies:
                    response.raw_cookies = {}

                    for cookie in response.cookies.jar:
                        response.raw_cookies[cookie.name] = cookie

            return response

    def _sanic_endpoint_test(
        self,
        method: str = "get",
        uri: str = "/",
        gather_request: bool = True,
        debug: bool = False,
        server_kwargs: typing.Optional[typing.Dict[str, typing.Any]] = None,
        host: str = None,
        *request_args,
        **request_kwargs,
    ) -> typing.Tuple[typing.Union[Request, HTTPResponse]]:
        results = [None, None]
        exceptions = []

        server_kwargs = server_kwargs or {"auto_reload": False}

        if gather_request:

            def _collect_request(request):
                if results[0] is None:
                    results[0] = request

            self.app.request_middleware.appendleft(_collect_request)

        @self.app.exception(MethodNotSupported)
        async def error_handler(request, exception):
            if request.method in ["HEAD", "PATCH", "PUT", "DELETE"]:
                return text(
                    "", exception.status_code, headers=exception.headers
                )
            else:
                return self.app.error_handler.default(request, exception)

        if self.port:
            server_kwargs = dict(
                host=host or self.host,
                port=self.port,
                **server_kwargs,
            )
            host, port = host or self.host, self.port
        else:
            sock = socket()
            sock.bind((host or self.host, 0))
            server_kwargs = dict(sock=sock, **server_kwargs)
            host, port = sock.getsockname()
            self.port = port

        if uri.startswith(
            ("http:", "https:", "ftp:", "ftps://", "//", "ws:", "wss:")
        ):
            url = uri
        else:
            uri = uri if uri.startswith("/") else f"/{uri}"
            scheme = "ws" if method == "websocket" else "http"
            url = f"{scheme}://{host}:{port}{uri}"
        # Tests construct URLs using PORT = None, which means random port not
        # known until this function is called, so fix that here
        url = url.replace(":None/", f":{port}/")

        @self.app.listener("after_server_start")
        async def _collect_response(sanic, loop):
            try:
                response = await self._local_request(
                    method, url, *request_args, **request_kwargs
                )
                results[-1] = response
                if method == "websocket":
                    await response.ws.close()
            except Exception as e:
                logger.exception("Exception")
                exceptions.append(e)
            finally:
                self.app.stop()

        self.app.run(debug=debug, **server_kwargs)
        self.app.listeners["after_server_start"].pop()

        if exceptions:
            raise ValueError(f"Exception during request: {exceptions}")

        if gather_request:
            try:
                request, response = results
                return request, response
            except BaseException:  # noqa
                raise ValueError(
                    f"Request and response object expected, got ({results})"
                )
        else:
            try:
                return results[-1]
            except BaseException:  # noqa
                raise ValueError(f"Request object expected, got ({results})")

    def request(self, *args, **kwargs):
        return self._sanic_endpoint_test("request", *args, **kwargs)

    def get(self, *args, **kwargs):
        return self._sanic_endpoint_test("get", *args, **kwargs)

    def post(self, *args, **kwargs):
        return self._sanic_endpoint_test("post", *args, **kwargs)

    def put(self, *args, **kwargs):
        return self._sanic_endpoint_test("put", *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self._sanic_endpoint_test("delete", *args, **kwargs)

    def patch(self, *args, **kwargs):
        return self._sanic_endpoint_test("patch", *args, **kwargs)

    def options(self, *args, **kwargs):
        return self._sanic_endpoint_test("options", *args, **kwargs)

    def head(self, *args, **kwargs):
        return self._sanic_endpoint_test("head", *args, **kwargs)

    def websocket(self, *args, **kwargs):
        return self._sanic_endpoint_test("websocket", *args, **kwargs)


class TestASGIApp(ASGIApp):
    async def __call__(self):
        await super().__call__()
        return self.request


async def app_call_with_return(self, scope, receive, send):
    asgi_app = await TestASGIApp.create(self, scope, receive, send)
    return await asgi_app()


class SanicASGITestClient(httpx.AsyncClient):
    def __init__(
        self,
        app: Sanic,
        base_url: str = ASGI_BASE_URL,
        suppress_exceptions: bool = False,
    ) -> None:
        app.__class__.__call__ = app_call_with_return
        app.asgi = True

        self.sanic_app = app

        transport = httpx.ASGITransport(app=app, client=(ASGI_HOST, ASGI_PORT))

        super().__init__(transport=transport, base_url=base_url)

        self.last_request = None

        def _collect_request(request):
            self.last_request = request

        @app.listener("after_server_start")
        def _start_test_mode(sanic, *args, **kwargs):
            sanic.test_mode = True

        @app.listener("before_server_end")
        def _end_test_mode(sanic, *args, **kwargs):
            sanic.test_mode = False

        app.request_middleware.appendleft(_collect_request)

    async def request(self, method, url, gather_request=True, *args, **kwargs):

        if not url.startswith(
            ("http:", "https:", "ftp:", "ftps://", "//", "ws:", "wss:")
        ):
            url = url if url.startswith("/") else f"/{url}"
            scheme = "ws" if method == "websocket" else "http"
            url = f"{scheme}://{ASGI_HOST}:{ASGI_PORT}{url}"

        self.gather_request = gather_request
        response = await super().request(method, url, *args, **kwargs)
        response.status = response.status_code
        response.body = response.content
        response.content_type = response.headers.get("content-type")

        return self.last_request, response

    async def websocket(self, uri, subprotocols=None, *args, **kwargs):
        scheme = "ws"
        path = uri
        root_path = f"{scheme}://{ASGI_HOST}:{ASGI_PORT}"

        headers = kwargs.get("headers", {})
        headers.setdefault("connection", "upgrade")
        headers.setdefault("sec-websocket-key", "testserver==")
        headers.setdefault("sec-websocket-version", "13")
        if subprotocols is not None:
            headers.setdefault(
                "sec-websocket-protocol", ", ".join(subprotocols)
            )

        scope = {
            "type": "websocket",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "headers": [map(lambda y: y.encode(), x) for x in headers.items()],
            "scheme": scheme,
            "root_path": root_path,
            "path": path,
            "query_string": b"",
            "subprotocols": subprotocols,
        }

        async def receive():
            return {}

        async def send(message):
            pass

        await self.sanic_app(scope, receive, send)

        return None, {"opened": True}
