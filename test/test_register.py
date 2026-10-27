from fastapi import FastAPI
from fastapi.testclient import TestClient
from main import app

cilent=TestClient(app)
def test_register():
    name="adm1"
    password="adadm1"
    response=cilent.post("/user_register",
                        headers={"content-type": "application/json"},
                        json={"username":name,"password":password},
                            )
    assert response.status_code==200
    assert response.json()["message"]=="注册成功"
def test_register_duplicate():
    name="adm"
    password="adm1"
    password1="adm2"
    cilent.post("/user_register",
                        headers={"content-type": "application/json"},
                        json={"username":name,"password":password},)
    response1=cilent.post("/user_register",
                            headers={"content-type": "application/json"},
                            json={"username":name,"password":password1},)
    assert response1.status_code==404
    assert response1.json()["detail"]=="用户名已存在"
def test_register_short_password():
    name="an"
    password="adad1"
    response=cilent.post("/user_register",
                        headers={"content-type": "application/json"},
                        json={"username":name,"password":password},
                                )
    assert response.status_code==422
def test_register_short_username():
    r = cilent.post("/user_register",
                    headers={"content-type": "application/json"},
                    json={"username":"ab","password":"pass123"})
    assert r.status_code == 422
