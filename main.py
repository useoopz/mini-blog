from fastapi import FastAPI,Depends
from fastapi.staticfiles import StaticFiles
import sqlite3
import time
from pydantic import BaseModel,Field

class AddPassage(BaseModel):
    title: str=Field(min_length=1)
    content: str=Field(min_length=1)

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
conn.close()
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
    
app.mount("/",StaticFiles(directory="frontend",html=True))#LOOKUPhttps://fastapi.tiangolo.com/zh/tutorial/static-files/#use-staticfiles
if __name__=="__main__":
    import uvicorn
    uvicorn.run("main:app",host="127.0.0.1",port=8000,reload=True)
