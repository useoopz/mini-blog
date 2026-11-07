def test_register(client):
    name="adm1"
    password="adadm1"
    response=client.post("/user_register",
                        headers={"content-type": "application/json"},
                        json={"username":name,"password":password},
                            )
    assert response.status_code==200
    assert response.json()["message"]=="注册成功"
def test_register_duplicate(client):
    name="adm"
    password="adm1"
    password1="adm2"
    client.post("/user_register",
                        headers={"content-type": "application/json"},
                        json={"username":name,"password":password},)
    response1=client.post("/user_register",
                            headers={"content-type": "application/json"},
                            json={"username":name,"password":password1},)
    assert response1.status_code==409
    assert response1.json()["detail"]=="用户名已存在"
def test_register_short_password(client):
    name="an"
    password="adad1"
    response=client.post("/user_register",
                        headers={"content-type": "application/json"},
                        json={"username":name,"password":password},
                                )
    assert response.status_code==422
def test_register_short_username(client):
    r = client.post("/user_register",
                    headers={"content-type": "application/json"},
                    json={"username":"ab","password":"pass123"})
    assert r.status_code == 422

def test_register_long_password(client):
    # bcrypt 只认前 72 字节，超长密码必须被参数层拦下，否则后半截形同虚设
    r = client.post("/user_register",
                    headers={"content-type": "application/json"},
                    json={"username":"longpw","password":"a"*73})
    assert r.status_code == 422

def test_login_long_password(client):
    # 登录口也要拦：bcrypt.checkpw 同样只认前 72 字节，
    # 不拦的话「正确密码 + 任意后缀」都能登进去
    name = "loginpw"
    password = "A"*72
    client.post("/user_register",
                headers={"content-type": "application/json"},
                json={"username":name,"password":password})
    r = client.post("/user_login",
                    data={"username":name,"password":password+"Z"*8})
    assert r.status_code == 422

def test_password_is_hashed(client):
    # 库里存的必须是哈希，不是明文
    from conftest import conn
    name = "hashcheck"
    password = "plain123"
    client.post("/user_register",
                headers={"content-type": "application/json"},
                json={"username":name,"password":password})
    row = conn.execute("SELECT hashpassword FROM user WHERE username=?", (name,)).fetchone()
    assert row is not None
    assert row[0] != password
    assert row[0].startswith("$2b$")
