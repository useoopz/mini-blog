import os
import jwt


def _forge_token(username):
    # 用真密钥签一个 token，但用户名不存在于库里 —— 模拟"密钥泄露后伪造身份"
    return jwt.encode({"username": username},
                      os.environ["MINI_BLOG_SECRET"],
                      algorithm="HS256")


def test_forged_username_rejected(client, token):
    # 先确认正常 token 能读
    r = client.get("/passage", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200

    # 伪造一个库里不存在的用户名，签名是真的
    fake = _forge_token("admin_owner")
    r = client.get("/passage", headers={"Authorization": f"Bearer {fake}"})
    assert r.status_code == 401


def test_forged_token_cannot_write(client, token):
    # 不只是读，写也必须挡住
    fake = _forge_token("admin_owner")
    r = client.post("/passage_add",
                    headers={"Authorization": f"Bearer {fake}"},
                    json={"title": "hacked", "content": "hacked"})
    assert r.status_code == 401

    # 而且库里真的没多出来
    left = client.get("/passage", headers={"Authorization": f"Bearer {token}"})
    assert all(p["title"] != "hacked" for p in left.json())


def test_forged_token_cannot_delete(client, token):
    # 删除也要挡 —— 这是最危险的一个
    client.post("/passage_add",
                headers={"Authorization": f"Bearer {token}"},
                json={"title": "t", "content": "c"})
    pid = client.get("/passage", headers={"Authorization": f"Bearer {token}"}).json()[0]["id"]

    fake = _forge_token("admin_owner")
    r = client.delete(f"/passage/{pid}", headers={"Authorization": f"Bearer {fake}"})
    assert r.status_code == 401

    # 原文还在
    left = client.get("/passage", headers={"Authorization": f"Bearer {token}"}).json()
    assert any(p["id"] == pid for p in left)
