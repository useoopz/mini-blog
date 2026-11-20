import socket
import httpx
import pytest

@pytest.mark.parametrize("bad_url", [
    "http://localhost:8000/docs",
    "http://192.168.1.1/admin",
    "http://10.0.0.1/internal",
    "http://169.254.169.254/latest/meta-data/",
    "file:///C:/Windows/win.ini",
])
def test_ssrf_block_private_and_scheme(client, token, monkeypatch, bad_url):
    async def fake_get(*args, **kwargs):
        raise AssertionError(f"SSRF 拦截失效，试图请求: {bad_url}")

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    r = client.post(
        "/passage_add",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "ces", "content": "ssrf_private", "url": bad_url},
    )
    assert r.status_code in (200,201)
    r1=client.get("/passage",headers={"Authorization": f"Bearer {token}"})
    title=[item["title"] for item in r1.json()["items"]]
    assert "ces" in title
    # TODO: 补充断言 r.status_code in (200, 201)，并通过查询列表接口验证文章正常创建

def test_ssrf_block_dns_spoofing(client, token, monkeypatch):
    # 模拟公网域名在 DNS 解析阶段返回本机回环地址 127.0.0.1
    def fake_getaddrinfo(host, port, *args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0))]

    async def fake_get(*args, **kwargs):
        raise AssertionError("DNS 欺骗拦截失效，发起了真实网络请求")

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    r=client.post("/passage_add",headers={"Authorization": f"Bearer {token}"},json={"title":"ces","content":"ces","url":"http://evil-public-domain.com/secret"})
    # TODO: 使用 "http://evil-public-domain.com/secret" 发起发帖请求并断言拦截降级成功
