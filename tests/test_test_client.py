from sanic.request import Request


def test_basic_test_client(app):
    request, response = app.test_client.get("/")

    assert isinstance(request, Request)
    assert response.body == b"foo"
    assert response.status == 200
    assert response.content_type == "text/plain; charset=utf-8"
