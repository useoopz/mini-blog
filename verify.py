"""手动验收工具：不开服务、不用 curl，直接打一遍接口看日志。

用法：
    D:\\code\\python\\python.exe verify.py
"""
import os
import warnings

os.environ.setdefault("MINI_BLOG_SECRET", "local_verify_secret_0123456789ab")
warnings.filterwarnings("ignore")

from fastapi.testclient import TestClient
import main

c = TestClient(main.app)

# 1) 注册一个随机用户（避免和已有用户名冲突）
import random
name = f"zz_verify_{random.randint(10000, 99999)}"
r = c.post("/user_register", json={"username": name, "password": "pass1234"})
print(f"[注册] {r.status_code} {r.text}")

# 2) 登录拿 token
r = c.post("/user_login", data={"username": name, "password": "pass1234"})
token = r.json()["access_token"]
print(f"[登录] {r.status_code} token={token[:20]}...")

h = {"Authorization": f"Bearer {token}"}

# 3) 打三个接口，看日志
print(f"[GET /passage] {c.get('/passage?page=1', headers=h).status_code}")
print(f"[GET /passage/mine] {c.get('/passage/mine', headers=h).status_code}")
print(f"[GET /nope] {c.get('/nope').status_code}")
