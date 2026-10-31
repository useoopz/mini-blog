from main import app

def test_post_without_token(client): 
    r=client.post("/passage_add",
                json={"title":"ces","content":"ces"})  
    assert r.status_code==401
    assert r.json()["detail"]=="Not authenticated"
def test_post_with_fake_token(client):    
    r=client.post("/passage_add",
                headers={"Authorization":"Bearer abccada"},
                json={"title":"ces","content":"ces"})  
    assert r.status_code==401
    assert r.json()["detail"]=="token无效或已过期"
def test_post_with_valid_token(client,token):   
    r=client.post("/passage_add",
                headers={"Authorization":f"Bearer {token}"},
                json={"title":"ces","content":"ces"})  
    assert r.status_code==200
    assert r.json()["message"]=="发布成功"