import sqlite3
import pytest
from main import app,get_db
conn=sqlite3.connect(":memory:" ,check_same_thread=False)
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
def override_get_db():
    yield conn
app.dependency_overrides[get_db] = override_get_db
@pytest.fixture(autouse=True)
def clear():
    conn.execute("DELETE FROM user")
    conn.execute("DELETE FROM passage")
    conn.commit()
    yield
    
    