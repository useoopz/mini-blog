from fastapi import FastAPI,Depends,HTTPException,Query,Request
from fastapi.staticfiles import StaticFiles
import sqlite3
import time
from pydantic import BaseModel,Field,field_validator
import bcrypt
import jwt
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
import os
import logging

class AddPassage(BaseModel):
    title: str=Field(min_length=1)
    content: str=Field(min_length=1)
class UserRegister(BaseModel):
    username: str=Field(min_length=3)
    password: str=Field(min_length=3)

    @field_validator("password")
    def validator_password(cls,name:str):
        if len(name.encode("utf-8")) > 72:
            raise ValueError("密码长度超过72字节")
        else:
            return name
app=FastAPI()
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    ms = (time.perf_counter() - start) * 1000
    log.info(f"{request.method} {request.url.path} {response.status_code} {ms:.1f}ms")
    return response
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", filename="app.log", encoding="utf-8")
log = logging.getLogger(__name__)
secret=os.environ["MINI_BLOG_SECRET"]
oauth2_scheme=OAuth2PasswordBearer(tokenUrl="/user_login")
conn=sqlite3.connect("mini-blog.db")
cursor=conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS passage(
id INTEGER PRIMARY KEY AUTOINCREMENT,
title TEXT,
content TEXT,
date TEXT,
author TEXT
)""" )#LOOKUPhttps://blog.csdn.net/m0_57545130/article/details/154491362#LOOKUPhttps://blog.csdn.net/chenlibao0823/article/details/104591359
conn.commit()
cursor.execute("""CREATE TABLE IF NOT EXISTS user(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT,
hashpassword TEXT
)""" )
conn.commit()
cursor.execute("PRAGMA table_info(passage)")
row=[r[1] for r in cursor.fetchall()]
if "author" not in row:
    cursor.execute("ALTER TABLE passage ADD COLUMN author TEXT")
    conn.commit()
cursor.execute("CREATE INDEX IF NOT EXISTS idx_author ON passage(author)")
conn.close()
def get_db():
    conn=sqlite3.connect("mini-blog.db")
    yield conn
    conn.close()#LOOKUPhttps://blog.csdn.net/mieleizhi0522/article/details/82142856
def get_current_user(token: str =Depends(oauth2_scheme),db=Depends(get_db)):
    try:
        payload=jwt.decode(token,secret,algorithms=["HS256"])
        cursor=db.cursor()
        cursor.execute("SELECT username FROM user WHERE username=?",(payload["username"],))
        if cursor.fetchone() is not None:
            return payload["username"]
        else:
            raise HTTPException(401,"token无效或已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(401,"token无效或已过期")
def hash_passaword(password):#LOOKUPhttps://docs.pingcode.com/baike/829063
    salt=bcrypt.gensalt()
    hashpassaword=bcrypt.hashpw(password.encode(),salt)
    return hashpassaword
@app.get("/passage")
def read_passage(db=Depends(get_db),current_user=Depends(get_current_user),page: int=Query(default=1,ge=1),page_size: int=Query(default=10,ge=1,le=100)):#LOOKUPhttps://blog.csdn.net/NeverLate_gogogo/article/details/112472480
    db.row_factory=sqlite3.Row
    cursor=db.cursor()
    cursor.execute("SELECT * FROM passage LIMIT ? OFFSET ?",(page_size,page_size*(page-1)))
    rows=cursor.fetchall()
    row=[dict(r) for r in rows]
    return row
@app.get("/passage/mine")
def read_passage_self(db=Depends(get_db),current_user=Depends(get_current_user),page: int=Query(default=1,ge=1),page_size: int=Query(default=10,ge=1,le=100)):
    db.row_factory=sqlite3.Row
    cursor=db.cursor()
    cursor.execute("SELECT * FROM passage WHERE author=? LIMIT ? OFFSET ? ",(current_user,page_size,page_size*(page-1)))
    rows=cursor.fetchall()
    row=[dict(r) for r in rows]
    return row
@app.post("/passage_add")
def passage_add(passage: AddPassage,db=Depends(get_db),current_user=Depends(get_current_user)):
    cursor=db.cursor()
    date=time.strftime("%Y-%m-%d %H-%M-%S",time.localtime())
    cursor.execute("INSERT INTO passage (title,content,date,author) VALUES (?,?,?,?)",(passage.title,passage.content,date,current_user))
    db.commit()
    return{"message":"发布成功"}
@app.post("/user_register")
def user_register(user:UserRegister,db=Depends(get_db)):#LOOKUPhttps://blog.csdn.net/Dxy1239310216/article/details/149141071
    cursor=db.cursor()
    cursor.execute("SELECT username FROM user WHERE username=?",(user.username,))
    row=cursor.fetchone()
    if row is not None:
        raise HTTPException(409,"用户名已存在")
    else:
        hashed=hash_passaword(user.password).decode()
        cursor.execute("INSERT INTO user (username,hashpassword) VALUES(?,?)",(user.username,hashed))
        db.commit()
        return{"message":"注册成功"}   
@app.post("/user_login")
def user_login(user:OAuth2PasswordRequestForm=Depends(),db=Depends(get_db)):
    if len(user.password.encode("utf-8")) > 72: raise HTTPException(422,"密码长度超出")
    cursor=db.cursor()
    cursor.execute("SELECT hashpassword FROM user WHERE username=?",(user.username,))
    row=cursor.fetchone() 
    if row is None:
        raise HTTPException(401,"用户名或密码错误")
    flag=bcrypt.checkpw(user.password.encode(),row[0].encode())
    if flag: 
        payload={"username":user.username,"exp":time.time()+3600}
        token=jwt.encode(payload,secret,algorithm="HS256")
        return{"message":"登陆成功","access_token":token}
    else:
        raise HTTPException(401,"用户名或密码错误")
@app.delete("/passage/{passage_id}")
def delete_passage(passage_id: int,db=Depends(get_db),current_user=Depends(get_current_user)):
    cursor=db.cursor()
    cursor.execute("SELECT author FROM passage WHERE id=?",(passage_id,))
    row=cursor.fetchone()
    if row is None:
        raise HTTPException(404,"文章不存在")
    if row[0] != current_user:
        raise HTTPException(403,"无权删除他人的文章")
    cursor.execute("DELETE FROM passage WHERE id=?",(passage_id,))
    db.commit()
    return{"message":"删除成功"}

app.mount("/",StaticFiles(directory="frontend",html=True))#LOOKUPhttps://fastapi.tiangolo.com/zh/tutorial/static-files/#use-staticfiles
if __name__=="__main__":
    import uvicorn
    uvicorn.run("main:app",host="0.0.0.0",port=8000,reload=True)
