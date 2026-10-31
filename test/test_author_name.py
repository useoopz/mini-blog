import uuid


def test_author(client, token, user):
    title = f"t_{uuid.uuid4().hex[:8]}"
    p = client.post("/passage_add",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"title": title, "content": "ces"})
    assert p.status_code == 200
    r = client.get("/passage", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    found = next((d for d in r.json() if d["title"] == title), None)
    assert found is not None, "没找到刚发的帖子"
    assert found["author"] == user[0]
