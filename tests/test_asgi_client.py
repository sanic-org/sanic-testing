import pytest

from sanic.request import Request

# @pytest.mark.asyncio
# async def test_post(app):
#     client = SanicASGITestClient(app)
#     _, response = await client.post(
#         "/", data=json.dumps({"foo": "bar"}), gather_request=False
#     )
#     assert response.status_code == 200
#     assert response.text == "123"

# from sanic_test import SanicASGITestClient
# import json


# @pytest.mark.asyncio
# async def test_get(app):
#     client = SanicASGITestClient(app)
#     _, response = await client.get("/", gather_request=False)
#     assert response.status_code == 200
#     assert response.text == "123"


@pytest.mark.asyncio
async def test_basic_asgi_client(app):
    request, response = await app.asgi_client.get("/")

    assert isinstance(request, Request)
    assert response.body == b"foo"
    assert response.status == 200
    assert response.content_type == "text/plain; charset=utf-8"
