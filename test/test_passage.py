def test_passage(client,token):
    r=client.get("/passage",headers={"Authorization": f"Bearer {token}"})
    assert r.status_code==200
    assert type(r.json())==list
def test_new_passage(client,token):
    for i in range(1,16):
        client.post("/passage_add",
                        headers={"Authorization":f"Bearer {token}"},
                        json={"title":f"ces{i}","content":"ces"})   
    r1 = client.get("/passage?page=1&page_size=5", headers={"Authorization": f"Bearer {token}"})
    ids1 = [j["id"] for j in r1.json()]     
    r2 = client.get("/passage?page=2&page_size=5", headers={"Authorization": f"Bearer {token}"})
    data2 = r2.json()
    assert len(data2) == 5
    assert data2[0]["id"] not in ids1
def test_wrong_passage(client,token):
    r=client.get("/passage?page=0",headers={"Authorization": f"Bearer {token}"})
    assert r.status_code==422

def test_empty_passage(client,token):
    # 空库必须返回 []，不是 None 也不是 500 —— 前端 for...in 直接崩在 None 上
    r=client.get("/passage",headers={"Authorization": f"Bearer {token}"})
    assert r.status_code==200
    assert r.json()==[]