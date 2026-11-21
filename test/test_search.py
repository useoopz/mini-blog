def test_passage_search(client,token):
    for i in range(2):
        client.post("/passage_add",
                        headers={"Authorization":f"Bearer {token}"},
                        json={"title":f"ces{i}","content":"ces"})
    client.post("/passage_add",
                            headers={"Authorization":f"Bearer {token}"},
                            json={"title":f"wu","content":"wu"})
    r=client.get("/passage/search",params={"q":"ces"},headers={"Authorization":f"Bearer {token}"})
    assert r.status_code==200
    assert len(r.json())==2
    r1=client.get("/passage/search",params={"q":"iii"},headers={"Authorization":f"Bearer {token}"})
    assert r1.status_code==200
    assert r1.json()==[]
    assert r.json()[0]["title"] == "ces1" and r.json()[1]["title"] == "ces0"
    r2=client.get("/passage/search",params={"q":""},headers={"Authorization":f"Bearer {token}"})
    assert r2.status_code==422
    r3=client.get("/passage/search",params={"q":"i"*51},headers={"Authorization":f"Bearer {token}"})
    assert r3.status_code==422
    r4=client.get("/passage/search",headers={"Authorization":f"Bearer {token}"})
    assert r4.status_code==422
    r5=client.get("/passage/search",params={"q":"i"*3})
    assert r5.status_code==401