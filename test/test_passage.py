def test_passage(client,token):
    r=client.get("/passage",headers={"Authorization": f"Bearer {token}"})
    assert r.status_code==200
    assert type(r.json())==list
