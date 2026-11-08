def _new_user(client, name):
    client.post("/user_register",
                headers={"content-type": "application/json"},
                json={"username": name, "password": "password"})
    r = client.post("/user_login",
                    headers={"content-type": "application/x-www-form-urlencoded"},
                    data={"username": name, "password": "password"})
    return r.json()["access_token"]


def _new_passage(client, token):
    client.post("/passage_add",
                headers={"Authorization": f"Bearer {token}"},
                json={"title": "t", "content": "c"})
    r = client.get("/passage", headers={"Authorization": f"Bearer {token}"})
    return r.json()[0]["id"]


def test_delete_own_passage(client, token):
    # 自己的文章能删，删完列表里就没了
    pid = _new_passage(client, token)
    r = client.delete(f"/passage/{pid}", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["message"] == "删除成功"
    left = client.get("/passage", headers={"Authorization": f"Bearer {token}"}).json()
    assert all(p["id"] != pid for p in left)


def test_delete_other_passage(client, token):
    # 别人不能删我的 —— 这是水平越权（IDOR）的唯一防线
    pid = _new_passage(client, token)
    other = _new_user(client, "otheruser")
    r = client.delete(f"/passage/{pid}", headers={"Authorization": f"Bearer {other}"})
    assert r.status_code == 403
    # 而且真的没被删掉
    left = client.get("/passage", headers={"Authorization": f"Bearer {token}"}).json()
    assert any(p["id"] == pid for p in left)


def test_delete_not_exist(client, token):
    r = client.delete("/passage/999999", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 404


def test_delete_without_token(client, token):
    pid = _new_passage(client, token)
    r = client.delete(f"/passage/{pid}")
    assert r.status_code == 401
