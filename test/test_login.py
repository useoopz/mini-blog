from main import app
from fastapi.testclient import TestClient

def test_login_success(client):
    name="adm1"
    password="adadm1"
    client.post("/user_register",
                headers={"content-type": "application/json"},
                json={"username":name,"password":password},
                )
    r=client.post("/user_login",
                         headers={"content-type": "application/x-www-form-urlencoded"},
                         data={"username":"adm1","password":"adadm1"})
    assert r.status_code==200
    assert r.json()["access_token"]
def test_login_wrong_password(client):
    name="adm1"
    password="adadm1"
    client.post("/user_register",
                headers={"content-type": "application/json"},
                json={"username":name,"password":password},
                )
    r=client.post("/user_login",
                headers={"content-type": "application/x-www-form-urlencoded"},
                data={"username":"adm1","password":"adadm1111"})
    assert r.status_code==401
    assert r.json()["detail"]=="用户名或密码错误"
def test_login_user_not_exist(client):
    r=client.post("/user_login",
                             headers={"content-type": "application/x-www-form-urlencoded"},
                             data={"username":"adm1","password":"adadm1"})
    assert r.status_code==401
    assert r.json()["detail"]=="用户名或密码错误"