from fastapi import FastAPI,Depends,HTTPException
from fastapi.staticfiles import StaticFiles
import sqlite3
import time
from pydantic import BaseModel,Field
import bcrypt
import jwt

class AddPassage(BaseModel):
    title: str=Field(min_length=1)
    content: str=Field(min_length=1)
class UserRegister(BaseModel):
    username: str=Field(min_length=3)
    password: str=Field(min_length=3)
class UserLogin(BaseModel):
    username: str
    password: str
app=FastAPI()

conn=sqlite3.connect("mini-blog.db")
cursor=conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS passage(
id INTEGER PRIMARY KEY AUTOINCREMENT,
title TEXT,
content TEXT,
date TEXT
)""" )#LOOKUPhttps://blog.csdn.net/m0_57545130/article/details/154491362#LOOKUPhttps://blog.csdn.net/chenlibao0823/article/details/104591359
conn.commit()
cursor.execute("""CREATE TABLE IF NOT EXISTS user(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT,
hashpassword TEXT
)""" )
conn.commit()
conn.close()
def hash_passaword(password):#LOOKUPhttps://docs.pingcode.com/baike/829063
    salt=bcrypt.gensalt()
    hashpassaword=bcrypt.hashpw(password.encode(),salt)
    return hashpassaword
def get_db():
    conn=sqlite3.connect("mini-blog.db")
    yield conn
    conn.close()#LOOKUPhttps://blog.csdn.net/mieleizhi0522/article/details/82142856
@app.get("/passage")
def read_passage(db=Depends(get_db)):#LOOKUPhttps://blog.csdn.net/NeverLate_gogogo/article/details/112472480
    db.row_factory=sqlite3.Row
    cursor=db.cursor()
    cursor.execute("SELECT * FROM passage")
    rows=cursor.fetchall()
    row=[dict(r) for r in rows]
    return row
@app.post("/passage_add")
def passage_add(passage: AddPassage,db=Depends(get_db)):
    cursor=db.cursor()
    date=time.strftime("%Y-%m-%d %H-%M-%S",time.localtime())
    cursor.execute("INSERT INTO passage (title,content,date) VALUES (?,?,?)",(passage.title,passage.content,date))
    db.commit()
    return{"message":"发布成功"}
@app.post("/user_register")
def user_register(user:UserRegister,db=Depends(get_db)):#LOOKUPhttps://blog.csdn.net/Dxy1239310216/article/details/149141071
    cursor=db.cursor()
    cursor.execute("SELECT username FROM user WHERE username=?",(user.username,))
    row=cursor.fetchone()
    if row is not None:
        raise HTTPException(404,"用户名已存在")
    else:
        hashed=hash_passaword(user.password).decode()
        cursor.execute("INSERT INTO user (username,hashpassword) VALUES(?,?)",(user.username,hashed))
        db.commit()
        return{"message":"注册成功"}   
@app.post("/user_login")
def user_login(user:UserLogin,db=Depends(get_db)):
    cursor=db.cursor()
    cursor.execute("SELECT hashpassword FROM user WHERE username=?",(user.username,))
    row=cursor.fetchone() 
    if row is None:
        raise HTTPException(401,"用户或密码错误")
    flag=bcrypt.checkpw(user.password.encode(),row[0].encode())
    if flag: 
        secret="my_now_secret"
        payload={"user_name":user.username,"exp":time.time()+3600}
        token=jwt.encode(payload,secret,algorithm="HS256")
        return{"message":"登陆成功","access_token":token}
    else:
        raise HTTPException(401,"用户或密码错误")
    
app.mount("/",StaticFiles(directory="frontend",html=True))#LOOKUPhttps://fastapi.tiangolo.com/zh/tutorial/static-files/#use-staticfiles
if __name__=="__main__":
    import uvicorn
    uvicorn.run("main:app",host="0.0.0.0",port=8000,reload=True)
