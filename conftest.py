import os
os.environ.setdefault("MINI_BLOG_SECRET", "5f3a9c1e7b2d4a6f8c0e1d3b5a7f9c2e4d6b8a0f1c3e5d7a9b2c4e6f8a0d1b3c")
import sqlite3
import pytest
from fastapi.testclient import TestClient
from main import app,get_db
import uuid
conn=sqlite3.connect(":memory:" ,check_same_thread=False)
cursor=conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS passage(
id INTEGER PRIMARY KEY AUTOINCREMENT,
title TEXT,
content TEXT,
date TEXT,
author TEXT
)""" )
conn.commit()
cursor.execute("""CREATE TABLE IF NOT EXISTS user(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT,
hashpassword TEXT
)""" )
conn.commit()
def override_get_db():
    yield conn
app.dependency_overrides[get_db] = override_get_db
@pytest.fixture(autouse=True)
def clear():
    conn.execute("DELETE FROM user")
    conn.execute("DELETE FROM passage")
    conn.commit()
    yield
@pytest.fixture
def client():
    return TestClient(app) 
@pytest.fixture
def user(client):
    name = f"u_{uuid.uuid4().hex[:8]}"
    password="password"
    client.post("/user_register",
                headers={"content-type": "application/json"},
                json={"username":name,"password":password},)
    return name,password
@pytest.fixture
def token(client, user):
    name,password=user
    r=client.post("/user_login",
                    headers={"content-type": "application/x-www-form-urlencoded"},
                    data={"username":name,"password":password},)   
    return r.json()["access_token"]
