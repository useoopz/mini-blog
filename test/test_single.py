def _new_user(client, name):
    # 注册一个用户，登录，把 token 交回去
    client.post("/user_register",
                headers={"content-type": "application/json"},
                json={"username": name, "password": "password"})
    r = client.post("/user_login",
                    headers={"content-type": "application/x-www-form-urlencoded"},
                    data={"username": name, "password": "password"})
    return r.json()["access_token"]


def _post(client, token, title):
    # 用某个用户的 token 发一篇文章
    client.post("/passage_add",
                headers={"Authorization": f"Bearer {token}"},
                json={"title": title, "content": "c"})


def test_mine_isolation(client):
    # 不用 conftest 的 token fixture，自己造两个用户
    ta = _new_user(client, "user_a")
    tb = _new_user(client, "user_b")

    # A 发 2 篇，B 发 1 篇
    _post(client, ta, "a1")
    _post(client, ta, "a2")
    _post(client, tb, "b1")

    # A 只看得到自己的 2 篇（不是 3 篇）
    ra = client.get("/passage/mine", headers={"Authorization": f"Bearer {ta}"})
    assert ra.status_code == 200
    assert len(ra.json()) == 2
    assert all(p["author"] == "user_a" for p in ra.json())

    # B 只看得到自己的 1 篇
    rb = client.get("/passage/mine", headers={"Authorization": f"Bearer {tb}"})
    assert rb.status_code == 200
    assert len(rb.json()) == 1
    assert all(p["author"] == "user_b" for p in rb.json())

    # 旧接口没被改坏：A 调 /passage 能看到全部 3 篇
    rall = client.get("/passage", headers={"Authorization": f"Bearer {ta}"})
    assert rall.status_code == 200
    assert len(rall.json()) == 3
