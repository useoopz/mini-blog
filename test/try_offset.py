import sqlite3
import time
conn=sqlite3.connect("offset.db")
cursor=conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS passage(
id INTEGER PRIMARY KEY AUTOINCREMENT,
title TEXT,
content TEXT,
date TEXT,
author TEXT
)""" )
conn.commit()
cursor.execute("""CREATE TABLE IF NOT EXISTS user(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT,
hashpassword TEXT
)""" )
conn.commit()
cursor.execute("CREATE INDEX IF NOT EXISTS author_idx  ON passage(author)")
before=time.perf_counter()
with conn:
    cursor.executemany("INSERT INTO passage (title,content,author,date) VALUES (?,?,?,?)",((f"title-{i}", f"content-{i}", f"author-{i}",f"date-{i}") for i in range(100_000) ))
after=time.perf_counter()
time1=(after-before)*1000
print(time1)
cursor.execute("EXPLAIN QUERY PLAN SELECT id, title, author FROM passage ORDER BY id DESC LIMIT 10 OFFSET 90000")
row=cursor.fetchall()
for i in row:
    print(i[3])
list1=[0, 10000, 50000, 90000]
for y in list1:
    before1=time.perf_counter()
    for x in range(50):
        cursor.execute("SELECT id, title, author FROM passage ORDER BY id DESC LIMIT 10 OFFSET ?",(y,))
        row=cursor.fetchall()
    after1=time.perf_counter()
    taltol=(after1-before1)*1000
    print(taltol)
    once=taltol/50
    print(once)
conn.close()

