import asyncio
from functools import partial
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Tuple

import httpx
from sanic import Sanic
from sanic.log import logger
from sanic.request import Request
from websockets.legacy.client import connect

from .testing import HOST, PORT, TestingResponse


class ReusableClient:
    def __init__(
        self,
        app: Sanic,
        host=HOST,
        port=PORT,
        loop=None,
        server_kwargs=None,
        client_kwargs=None,
    ):
        if not loop:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        server_kwargs = server_kwargs or {}
        client_kwargs = client_kwargs or {}

        app.test_mode = True
        self.app = app
        self.host = host
        self.port = port
        self._loop = loop
        self.debug = False
        self._server = None

        self._session = httpx.AsyncClient(verify=False, **client_kwargs)
        self._server_co = self.app.create_server(
            host=self.host,
            debug=self.debug,
            port=self.port,
            return_asyncio_server=True,
            **server_kwargs,
        )

    def __enter__(self):
        self.run()

    def __exit__(self, *_):
        self.stop()

    def run(self):
        self._loop._stopping = False
        self.app.router.reset()
        self.app.signal_router.reset()
        self._run(self.app._startup())
        self._run(self.app._server_event("init", "before", loop=self._loop))
        self._server = self._run(self._server_co)
        self._run(self.app._server_event("init", "after", loop=self._loop))

    def stop(self):
        self._run(
            self.app._server_event("shutdown", "before", loop=self._loop)
        )
        if self._server:
            self._server.close()
            self._run(self._server.wait_closed())
            self._server = None

        if self._session:
            self._run(self._session.aclose())
            self._session = None
        self._run(self.app._server_event("shutdown", "after", loop=self._loop))

    def _sanic_endpoint_test(
        self,
        method: str = "get",
        uri: str = "/",
        gather_request: bool = True,
        debug: bool = False,
        server_kwargs: Optional[Dict[str, Any]] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        allow_none: bool = False,
        *request_args,
        **request_kwargs,
    ) -> Tuple[Optional[Request], Optional[TestingResponse]]:
        request_data: Dict[str, Request] = {}
        exceptions: List[Exception] = []

        host = host or self.host
        port = port or self.port

        if gather_request:
            _collect_request = partial(self._collect_request, request_data)
            self.app.request_middleware.appendleft(  # type: ignore
                _collect_request
            )

        if uri.startswith(
            ("http:", "https:", "ftp:", "ftps://", "//", "ws:", "wss:")
        ):
            url = uri
        else:
            uri = uri if uri.startswith("/") else f"/{uri}"
            scheme = "ws" if method == "websocket" else "http"
            url = f"{scheme}://{host}:{port}{uri}"

        if exceptions:
            raise ValueError(f"Exception during request: {exceptions}")

        response = self._run(
            self._local_request(method, url, *request_args, **request_kwargs)
        )

        try:
            self.app.request_middleware.remove(  # type: ignore
                _collect_request
            )
        except BaseException:  # noqa
            pass

        try:
            request = request_data.get("request") if gather_request else None
            if response is None:
                if not allow_none:
                    raise ValueError(
                        "No response returned to Sanic Test Client."
                    )
            return request, response
        except BaseException:  # noqa
            if not allow_none:
                raise ValueError(
                    "Request and response object expected, "
                    f"got ({request}, {response})"
                )

        return None, None

    async def _local_request(self, method, url, *args, **kwargs):
        raw_cookies = kwargs.pop("raw_cookies", None)

        if method == "websocket":
            ws_proxy = SimpleNamespace()
            async with connect(url, *args, **kwargs) as websocket:
                ws_proxy.ws = websocket
                ws_proxy.opened = True
            return ws_proxy
        else:
            session = self._session

            try:
                if method == "request":
                    args = tuple([url] + list(args))
                    url = kwargs.pop("http_method", "GET").upper()
                response = await getattr(session, method.lower())(
                    url, *args, **kwargs
                )
            except httpx.HTTPError as e:
                if hasattr(e, "response"):
                    response = getattr(e, "response")
                else:
                    logger.error(
                        f"{method.upper()} {url} received no response!",
                        exc_info=True,
                    )
                    return None

            response.__class__ = TestingResponse

            if raw_cookies:
                response.raw_cookies = {}

                for cookie in response.cookies.jar:
                    response.raw_cookies[cookie.name] = cookie

            return response

    def _run(self, coro):
        if not self._loop:
            raise RuntimeError("Test client has no loop")
        return self._loop.run_until_complete(coro)

    @staticmethod
    def _collect_request(data, request):
        data["request"] = request

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
