import sqlite3
import time
conn=sqlite3.connect("offset.db")
cursor=conn.cursor()
cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM passage WHERE id < ? ORDER BY id DESC LIMIT 10",(10001,))
row1=cursor.fetchall()
print(row1)
began=time.perf_counter()
for i in range(50):
    for j in range(10):
        cursor.execute("SELECT * FROM passage WHERE id < ? ORDER BY id DESC LIMIT 10",(10001,))
        row=cursor.fetchall()

after=time.perf_counter()
time1=(after-began)*1000
print(time1/50)
conn.close()