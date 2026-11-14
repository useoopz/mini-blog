from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from main import app


def _boom():
    return 1 / 0


def test_boom_returns_clean_500():
    """接口炸了，客户端只能拿到一句人话，拿不到 traceback。"""
    # main.py 末尾 app.mount("/") 会接管所有未匹配路径，
    # 所以临时路由必须插到最前面，否则会先被静态文件兜成 404。
    route = APIRoute("/boom", _boom, methods=["GET"])
    app.router.routes.insert(0, route)
    try:
        c = TestClient(app, raise_server_exceptions=False)
        r = c.get("/boom")

        assert r.status_code == 500
        assert r.json() == {"detail": "服务器内部错误"}

        body = r.text
        assert "ZeroDivisionError" not in body
        assert "Traceback" not in body
        assert ".py" not in body
    finally:
        app.router.routes.remove(route)
