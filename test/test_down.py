import main
async def fake_fetch(url: str) -> str:
    return ""

def test_send_passage(client,token,monkeypatch):
    monkeypatch.setattr(main, "fetch_title", fake_fetch)
    r=client.post("/passage_add",
                            headers={"Authorization":f"Bearer {token}"},
                            json={"title":"ces","content":"ces","url": "http://example.com"}) 
    assert r.status_code==201
    r1=client.get("/passage",headers={"Authorization":f"Bearer {token}"})
    titles = [item["title"] for item in r1.json()]
    assert "ces" in titles