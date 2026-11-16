def _new_user(client, name):
    client.post("/user_register",
                headers={"content-type": "application/json"},
                json={"username": name, "password": "password"})
    r = client.post("/user_login",
                    headers={"content-type": "application/x-www-form-urlencoded"},
                    data={"username": name, "password": "password"})
    return r.json()["access_token"]


def _new_passage(client, token, title="t", content="c"):
    client.post("/passage_add",
                headers={"Authorization": f"Bearer {token}"},
                json={"title": title, "content": content})
    r = client.get("/passage", headers={"Authorization": f"Bearer {token}"})
    return r.json()[0]["id"]


def test_update_own_passage(client, token):
    # 改自己的文章：不光状态码是 200，库里的内容必须真的变了
    pid = _new_passage(client, token, title="旧标题", content="旧正文")
    r = client.put(f"/passage/{pid}",
                   headers={"Authorization": f"Bearer {token}"},
                   json={"title": "新标题", "content": "新正文"})
    assert r.status_code == 200

    rows = client.get("/passage", headers={"Authorization": f"Bearer {token}"}).json()
    found = next((p for p in rows if p["id"] == pid), None)
    assert found is not None, "改完之后文章不见了"
    assert found["title"] == "新标题"
    assert found["content"] == "新正文"


def test_update_keeps_date(client, token):
    # date 是发布时间，改内容不应该把它冲掉
    pid = _new_passage(client, token, title="原标题")
    before = next(p for p in client.get("/passage",
                   headers={"Authorization": f"Bearer {token}"}).json() if p["id"] == pid)

    client.put(f"/passage/{pid}",
               headers={"Authorization": f"Bearer {token}"},
               json={"title": "改过的标题", "content": "c"})

    after = next(p for p in client.get("/passage",
                  headers={"Authorization": f"Bearer {token}"}).json() if p["id"] == pid)
    assert after["date"] == before["date"]


def test_update_other_passage(client, token):
    # 别人不能改我的 —— 改成功比删掉更危险
    pid = _new_passage(client, token, title="我的文章")
    other = _new_user(client, "otheruser")

    r = client.put(f"/passage/{pid}",
                   headers={"Authorization": f"Bearer {other}"},
                   json={"title": "被改了", "content": "被改了"})
    assert r.status_code == 403

    rows = client.get("/passage", headers={"Authorization": f"Bearer {token}"}).json()
    found = next(p for p in rows if p["id"] == pid)
    assert found["title"] == "我的文章", "403 之后内容居然被改了"


def test_update_not_exist(client, token):
    r = client.put("/passage/999999",
                   headers={"Authorization": f"Bearer {token}"},
                   json={"title": "x", "content": "x"})
    assert r.status_code == 404


def test_update_without_token(client, token):
    pid = _new_passage(client, token)
    r = client.put(f"/passage/{pid}", json={"title": "x", "content": "x"})
    assert r.status_code == 401


def test_update_empty_title(client, token):
    pid = _new_passage(client, token)
    r = client.put(f"/passage/{pid}",
                   headers={"Authorization": f"Bearer {token}"},
                   json={"title": "", "content": "x"})
    assert r.status_code == 422
    # 被拒了就不该改到库里
    rows = client.get("/passage", headers={"Authorization": f"Bearer {token}"}).json()
    assert next(p for p in rows if p["id"] == pid)["title"] != ""

def test_update_commits(client, token, conn_):
    # 事务没提交 = 改动会被回滚。内存库看不出这点，只能看连接还有没有未提交事务
    pid = _new_passage(client, token, title="原标题")
    conn_.commit()  # 先把之前攒的清干净
    assert not conn_.in_transaction, "前置条件：跑之前不该有悬挂事务"

    r = client.put(f"/passage/{pid}",
                   headers={"Authorization": f"Bearer {token}"},
                   json={"title": "新标题", "content": "c"})
    assert r.status_code == 200
    assert not conn_.in_transaction, "PUT 里的 UPDATE 没 commit，事务悬挂着"
