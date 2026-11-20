def test_passage(client,token):
    r=client.get("/passage",headers={"Authorization": f"Bearer {token}"})
    assert r.status_code==200
    assert r.json()["items"]==[]
    assert r.json()["next_cursor"] is None
    assert r.json()["has_more"] is False
def test_new_passage(client,token):
        for i in range(5):
            client.post("/passage_add",
                        headers={"Authorization":f"Bearer {token}"},
                        json={"title":f"ces{i}","content":"ces"}) 
        res=client.get("/passage?limit=2",headers={"Authorization": f"Bearer {token}"}) 
        nxt=res.json()["next_cursor"]
        r=client.get("/passage",params={"cursor":nxt,"limit": 2},headers={"Authorization": f"Bearer {token}"})
        nxt1=r.json()["next_cursor"]
        r1=client.get("/passage",params={"cursor":nxt1,"limit": 2},headers={"Authorization": f"Bearer {token}"})
        assert r1.json()["next_cursor"] is None
        assert r1.json()["has_more"] is False
def test_wrong_passage(client,token):
    r=client.get("/passage",params={"cursor":1,"limit": 2},headers={"Authorization": f"Bearer {token}"})
    assert r.json()["next_cursor"] is None
    assert r.json()["has_more"] is False
def test_empty_passage(client,token):
    r=client.get("/passage",params={"cursor":0,"limit": 2},headers={"Authorization": f"Bearer {token}"})
    assert r.status_code==422
    r1=client.get("/passage",params={"cursor":3,"limit": 0},headers={"Authorization": f"Bearer {token}"})
    assert r1.status_code==422
    r2=client.get("/passage",params={"cursor":3,"limit": 51},headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code==422