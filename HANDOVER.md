# mini-blog 项目交接文档

> **生成日期**：2026-10-18（最后更新 2026-10-31）
> **资料来源**：`.workbuddy/memory/` 下的 `MEMORY.md` 与 `2026-10-12 ~ 2026-10-30` 每日日志
> **读者**：接手这个项目的人（或隔一段时间回来的作者本人）
> **阅读建议**：赶时间只看 §0；接手第一天照 §7 做；测试相关直接看 §9

---

## 0. 30 秒速览

| 项 | 内容 |
|---|---|
| **是什么** | 一个**从零手写**的迷你博客：注册 / 登录 / 发帖 / 看文章。FastAPI + SQLite + 原生 JS，无框架 |
| **在哪** | `D:\mini-blog\`（本地）｜`https://github.com/useoopz/mini-blog`（公开） |
| **能跑什么** | 未登录跳登录页；注册 → 登录拿 token → 首页显示全部文章（带作者名）；填标题+正文点提交，写库并自动刷新；空标题被后端拒绝并弹提示 |
| **代码量（2026-10-31 实测）** | `main.py` 104 行 / `frontend/` 三个页面 68+47+42 行 / `conftest.py` 50 行 / `test/` 五个文件 101 行 |
| **当前状态** | 能跑、有 JWT 鉴权、**12 个测试全绿**、secret 已进环境变量、`requirements.txt` 补全、注册重名返回 409。**没有分页、没有 CSS、没有编辑删除** |
| **下一步** | 部署周 Day 21-25：买/复用服务器 → 装环境传代码 → systemd 守护 |

**一分钟跑起来**：
```bash
cd D:\mini-blog
D:\code\python\python.exe -m uvicorn main:app --reload
# 浏览器打开 http://127.0.0.1:8000/
```

---

## 1. 项目背景与目标

### 1.1 这是什么

一个**可以发文章、看文章**的极简博客。两个页面动作，两个接口。

技术上刻意保持"原始"：

- **不用框架** —— 没有 Vue/React，前端是手写 HTML + 原生 `fetch` + DOM API
- **不用 ORM** —— 直接 `sqlite3` 写 SQL
- **不用脚手架** —— 没有 cookiecutter / 项目模板，文件是手建的空文件

### 1.2 为什么做它（这一点比代码重要）

这个项目**不是为了"做一个博客"**。

作者之前已经有一个功能更完整的博客（`D:\博客代码\`，13 个接口、登录、评论、两条线上线），**但那个是跟着 AI 一步步做出来的**。

`mini-blog` 的真实目的是：**证明"关掉 AI 也能独立做出东西"**。

所以它有一条**贯穿始终的规则**（见 §6.4），违反了项目就失去意义。

### 1.3 验收判据与达成情况

| 判据 | 状态 |
|---|---|
| 能跑起来 | ✅ |
| 每个文件能说出职责 | ✅（Day 5 补测，见 §3.5） |
| 报错能自己定位 | ✅（§4 的每个问题都是自己查出来的） |

---

## 2. 已完成的工作与关键决策

### 2.1 时间线

| 天 | 日期 | 做了什么 |
|---|---|---|
| Day 1 | 10-12 | 骨架：建 `main.py` / `requirements.txt` / `index.html`，只会"按图发文件" |
| Day 2 | 10-13 | 接数据库：`mini-blog.db` + `passage` 表；`GET /passage` 返回 JSON |
| Day 3 | 10-14 | 加"写"：`POST /passage_add`；首页接上后端，**文章第一次上屏** |
| Day 4 | 10-15 | 每条显示自己的字段；接口从"数组套数组"改成**对象列表**；地址去写死（根相对）；**发帖表单** |
| Day 5 | 10-16 | **反静默**：后端会拒绝（`Field(min_length=1)` → 422）、前端会说话（`response.ok` + 弹提示） |
| Day 6 | 10-17 | **建 Git 仓库 + 上 GitHub**；算法开个头（LeetCode 1） |
| Day 7 | 10-18 | 修完两数之和（0ms）+ 217；**curl 攻坚**（PS 5.1 别名 / 引号被吃 / BOM 三个坑）；写 README 并 push |
| Day 8-10 | 10-19 ~ 10-21 | 用户系统：`/user_register`（bcrypt）、`/user_login`（OAuth2 表单 + JWT）、`get_current_user` 鉴权；`author` 字段迁移（`PRAGMA table_info` + `ALTER TABLE`） |
| Day 11-15 | 10-22 ~ 10-26 | 前端三页：`index.html` 门禁、`login.html`、`register.html`；401 分支与 `err.detail` 分型显示；算法刷到 20 题 |
| Day 16-18 | 10-27 ~ 10-29 | **pytest 从零**：`ModuleNotFoundError` 排查、内存库隔离、`dependency_overrides`、三个 fixture |
| Day 19-20 | 10-30 | `test_auth.py` 三用例补齐 → **10 个测试全绿**；496 单调栈；本文档补 §9 |
| Day 21 | 10-31 | LeetCode 206 手写通过；**技术债清理日**：补 `GET /passage` + author 落库两个测试（→12 个）、secret 进环境变量、`requirements.txt` 补 bcrypt+PyJWT 修行尾、注册重名 404→409；做了一次变异测试 |

### 2.2 关键决策（每条都有代价，不是"最佳实践"）

| 决策 | 结论 | 理由 | 代价 |
|---|---|---|---|
| 前端托管方式 | 后端用 `mount("/")` 顺手托管前端 | **前后端同源 → 不触发 CORS**，也不用开第二个服务 | `mount("/")` **必须放所有路由之后**，否则吞掉接口（§4-#1） |
| 数据库连接 | `get_db()` **每个请求新建一条**，`yield` + `close` | 多人同时访问时各拿各的，不抢同一份 | 每请求一点连接开销（SQLite 本地可忽略） |
| 读接口返回格式 | **对象列表** `[{"id":8,"title":…}]` | 前端能按**名字**取字段；靠位置取（`j[1]`）改表就错，而且**不报错** | 后端多一步 `[dict(r) for r in rows]` |
| 写接口校验位置 | 校验放**后端**（`Field(min_length=1)`） | 前端的检查只是体验优化，**任何人都能绕过网页直接 curl** | 前端要单独再写一遍提示逻辑（重复，但必要） |
| 前端渲染方式 | `createElement` + `textContent` + `appendChild`，**不用 `innerHTML` 拼字符串** | 要显示的是**用户输入的内容**，拼 HTML 会执行别人的代码（XSS） | 代码比 `innerHTML` 长 |
| 重画列表 | 每轮渲染前 `list.innerHTML = ""` | 不清空会**在原列表上再叠一遍**（§4-#6） | 无 |
| 请求地址 | **根相对** `/passage`，不写 `http://127.0.0.1:8000/passage` | 换端口、换域名、部署到服务器都自动跟随 | 无 |
| 按钮绑定 | `<button onclick="add_passage()">` | 最快跑通，零新 API | HTML 与 JS 耦合；将来可换 `addEventListener` |
| 数据库文件 | **不进 Git**（`*.db` 写进 `.gitignore`） | 二进制存不出差异、每发一帖就变、协作没法合并；且 `CREATE TABLE IF NOT EXISTS` 能自建空库 | 克隆下来是空的，要自己发几篇才有数据 |

---

## 3. 代码结构与重要模块

### 3.1 目录

```
D:\mini-blog\
├── main.py               104 行 · 整个后端（模型 / 建表 / 鉴权 / 6 个路由 / 静态托管）
├── requirements.txt      4 个包（fastapi / uvicorn / bcrypt / PyJWT）LF 行尾
├── conftest.py           50 行 · 测试夹具（内存库 + 4 个 fixture + 测试用 secret）
├── test/
│   ├── test_register.py  34 行 · 注册四用例（含重名 409）
│   ├── test_login.py     30 行 · 登录三用例
│   ├── test_auth.py      19 行 · 鉴权三用例
│   ├── test_passage.py    4 行 · 读接口形状
│   └── test_author_name.py 14 行 · author 真的落库了
├── .gitignore            __pycache__/  *.db  post.json
├── mini-blog.db          SQLite 数据库（不进仓库，两张表 passage / user）
├── HANDOVER.md          本文档
├── README.md            面向陌生人的项目说明
├── frontend/
│   ├── index.html        68 行 · 首页（门禁 + 列表 + 发帖）
│   ├── login.html        47 行 · 登录页
│   └── register.html     42 行 · 注册页
└── __pycache__/          Python 缓存（不进仓库）
```

### 3.2 `main.py` —— 一个文件装了六件事（**按执行顺序**）

| 区段 | 行 | 干什么 | 关键点 |
|---|---|---|---|
| **① 配置与模型** | 1-22 | `secret`、`oauth2_scheme`、`AddPassage` / `UserRegister` / `UserLogin` 三个模型 | `secret=os.environ["MINI_BLOG_SECRET"]`（21 行，**没设环境变量就启动即崩**，这是故意的）；`UserLogin`（17-19 行）**目前没被任何路由用到**，是残留 |
| **② 一次性初始化** | 23-44 | 连库 → 建 `passage` / `user` 两张表 → **`PRAGMA table_info` 检查 `author` 列** → 缺则 `ALTER TABLE` 补 | 这段在**模块级**，启动只跑一次。`CREATE TABLE IF NOT EXISTS` **不会改旧表**，所以加字段必须走 `ALTER` |
| **③ 鉴权依赖** | 45-50 | `get_current_user()`：`jwt.decode` → 失败抛 401 | `except jwt.InvalidTokenError` → `"token无效或已过期"` |
| **④ 连接工厂与哈希** | 51-58 | `hash_passaword()`（bcrypt 加盐）、`get_db()`（每请求新建连接，`yield` → `close`） | `yield conn` 而不是 `yield conn.close()`（§4 坑一）。⚠️ 函数名 `hash_passaword` 拼错，全项目沿用，改名前先全局搜 |
| **⑤ 六个路由** | 59-99 | 读文章 / 发文章 / 注册 / 登录 | **全部在 `mount("/")` 之前** |
| **⑥ 静态托管** | 101 | `mount("/", StaticFiles(directory="frontend", html=True))` | **必须在所有路由之后** |
| **⑦ 启动块** | 102-104 | `uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)` | 已改 `0.0.0.0` ✅ |

**路由清单**

| 方法 | 路径 | 请求体格式 | 鉴权 | 返回 |
|---|---|---|---|---|
| POST | `/user_register` | **JSON** `{"username","password"}` | 无 | `{"message":"注册成功"}` / **409** 用户名已存在 / 422 字段太短 |
| POST | `/user_login` | **表单** `username=..&password=..` | 无 | `{"message":"登陆成功","access_token":"...","token_type":"bearer"}` / 401 用户或密码错误 |
| GET | `/passage` | — | ✅ 要 token | 对象列表（含 `author`） |
| POST | `/passage_add` | **JSON** `{"title","content"}` | ✅ 要 token | `{"message":"发布成功"}` / 422 |

> ⚠️ **注册收 JSON、登录收表单**，这是 `OAuth2PasswordRequestForm` 的要求，前端两页写法不同就是这个原因。

**两个接口的细节**

```
GET  /passage
     db.row_factory = sqlite3.Row      ← ⚠️ 必须在 cursor = db.cursor() 之前
     cursor = db.cursor()
     rows = cursor.fetchall()
     return [dict(r) for r in rows]    ← 每行转字典，得到"对象列表"

POST /passage_add
     请求体：{"title": "...", "content": "..."}
     date 由服务端生成（time.strftime）
     author = current_user（来自 token）
     INSERT INTO passage (title, content, date, author) VALUES (?,?,?,?)
     返回 {"message":"发布成功"}
     校验失败 → 422，响应体含 detail[0].msg
```

### 3.3 `frontend/index.html` —— 两个角色合一

| 角色 | 部分 | 内容 |
|---|---|---|
| **形状** | HTML | 两个 `<input>`（`id="title"` / `id="content"`）+ `<button onclick>` + `<ul id="list">` |
| **行为** | `<script>` | 两个函数：`passage()` 读、`add_passage()` 写 |

```
passage()          →  GET /passage → 清空 <ul> → 逐条造 <li> 挂上去
add_passage()      →  读两个输入框的 .value
                   →  POST /passage_add（body 用 JSON.stringify）
                   →  response.ok 为真 → 调 passage() 刷新
                   →  为假 → alert(err.detail[0].msg)  ← 把后端原话给用户看
```

**页面加载时**末尾有一行 `passage()` —— **没有它页面就是空的**（函数定义了不等于会执行）。

### 3.4 `requirements.txt` 与数据库

- `requirements.txt`：`fastapi==0.141.1` / `uvicorn==0.52.4`
  - **fastapi** = 用来写应用的框架（路由、数据校验）
  - **uvicorn** = 真正把服务跑起来、守端口收 HTTP 的那个进程
  - 实际安装版本（2026-10-31 实测）：`fastapi 0.141.1` / `uvicorn 0.52.4` / **`pydantic 2.13.5`** / `bcrypt 4.0.1` / `PyJWT 2.13.0` / `pytest 9.1.1` / `httpx 0.28.1`
  - ✅ 2026-10-31：`requirements.txt` 已补齐四个运行必需包（`fastapi` / `uvicorn` / `bcrypt` / `PyJWT`），行尾从 CR-only 改成 LF。`pip install -r requirements.txt --dry-run` 四行全 `Requirement already satisfied`
  - ⚠️ **`pytest` / `httpx` 还没进任何 requirements 文件** —— 换机器能跑服务，但跑不了测试
- `passage` 表：`id INTEGER PRIMARY KEY AUTOINCREMENT` / `title TEXT` / `content TEXT` / `date TEXT` / `author TEXT`
- `user` 表：`id INTEGER PRIMARY KEY AUTOINCREMENT` / `username TEXT` / `hashpassword TEXT`
  - ⚠️ `username` **没有 UNIQUE 约束**，重复判断靠代码里的 `SELECT ... WHERE username=?`；并发下会有竞态
- `.db` 不进仓库，克隆后靠 `CREATE TABLE IF NOT EXISTS` 自建空表；**但加字段不会自动生效**，要靠启动时的 `PRAGMA table_info` + `ALTER TABLE`

### 3.5 一句话职责（原作者口述，已校对）

| 文件 | 职责 |
|---|---|
| `main.py` | 服务器收到请求后做什么：建库建表 → 定数据形状 → 验身份 → 收请求 → 查/写 → 回结果 |
| `frontend/index.html` | 首页：门禁（没 token 跳登录）+ 列表 + 发帖 |
| `frontend/login.html` / `register.html` | 登录 / 注册表单，成功后把 token 存进 `localStorage` |
| `conftest.py` | 测试的"假环境"：内存库 + 假浏览器 + 现成账号 + 现成 token |
| `requirements.txt` | 换台机器，靠它把环境装起来 |
| `mini-blog.db` | 数据存在哪 |

> 原作者的原始答案漏了"数据层"和"数据模型"（只说"路由+挂载"），§3.2 已补全 —— 说明**这块是他最不熟的部分**。

---

## 4. 遇到的问题及解决方式（**本节最有价值**）

每条都是真实踩过的，按"现象 → 真根因 → 怎么验证 → 怎么修"记录。

### #1 接口突然全 404，但代码看着没问题

- **现象**：加了路由却打不开，或者首页把接口吞了
- **真根因**：Starlette **先注册先匹配**。`mount("/")` 写在路由前面 → 它接管一切
- **验证**：`curl` 每个端点看状态码；`GET /passage_add` 返回 **404 而不是 405**，就是被 `mount("/")` 当成"找静态文件"了
- **修**：所有路由 → `mount("/static")` → **`mount("/")` 放最末**

### #2 中文进库变成 `???`

- **现象**：用 PowerShell 发帖，库里存的是 `'???'`；浏览器和终端也显示乱码
- **真根因**：**PowerShell 5.1 在请求没有 `charset` 时，上下行都默认 ISO-8859-1（Latin-1）**
  - 上行：中文编不了 → 每字替换成 `?` → **库里真的坏了**
  - 下行：服务器发的是 UTF-8，PS 按 Latin-1 解 → **只是显示坏，数据是好的**
- **验证**：**读库里的 `repr`**（`'??'` vs `'乙组中文正常'`），不看终端
  - ⭐ 关键证据：`'没有charset'` → 库里变成 `'??charset'` —— **ASCII 活着，只有中文死了**
- **修**：`Invoke-RestMethod -ContentType "application/json; charset=utf-8"`
- **教训**：**两个"乱码"长得一样，本质不同。判据要放数据源，不放屏幕。**

### #3 加了 `row_factory` 却没用，接口 500

- **现象**：`ValueError: dictionary update sequence element #0 has length 4; 2 is required`
- **真根因（两层）**：
  1. `dict(rows)` 把**一堆行**整个丢给 `dict()` —— 它要的是"一串键值对（每对 2 格）"
  2. **`cursor` 在创建那一刻就抄走了连接的 `row_factory`** → 之后设 `db.row_factory` 对已存在的 cursor **无效**
- **验证**：
  ```python
  cur = c.cursor(); c.row_factory = sqlite3.Row   # 先建后设
  print(type(cur.fetchone()).__name__)            # → tuple（没生效！）
  ```
- **修**：`db.row_factory = sqlite3.Row` **放在 `db.cursor()` 之前**；返回改成 `[dict(r) for r in rows]`
- **教训**：**"设了等于没设"没有任何报错** —— 静默家族的一员

### #4 前端写死 `http://127.0.0.1:8000`，换端口就空

- **现象**：把服务换到 8899 端口，页面打得开但列表空白
- **真根因**：**`127.0.0.1` 指的是"正在解析它的那台机器"**。这行 `fetch` 是**访客的浏览器**在跑 → 它去找**访客自己的电脑**
  - 本地开发时"跑服务的机器 == 开浏览器的机器"，两个身份重合，所以看不出问题
  - 部署后两个身份分开 → 必炸
- **验证**：换 8899 起服务，开 `http://127.0.0.1:8899/` → 页面来了，但 `fetch` 还去敲 8000（8000 已停）→ 空白 + 控制台网络错误
- **修**：改成根相对 `"/passage"` —— 浏览器会用**当前页面的来源**补全，谁在哪打开它就跟谁走

### #5 每次点提交，列表重复一遍（10 条、15 条…）

- **现象**：发一帖，列表在原基础上又叠一遍全部文章
- **真根因**：`passage()` **只会往里加，从不清空**。它只在页面加载时被调用一次，所以之前没暴露
- **验证**：**刷新页面重复就消失**（重画时容器是空的）→ 说明是**渲染层**问题，不是库
- **修**：循环之前 `list.innerHTML = ""`
- **教训**：**判据 —— "这个函数被调第二次会怎样？"** 只适合调一次的函数在真实项目里几乎没用

### #6 空标题能发出去，库里躺了一条没标题的记录

- **现象**：标题留空提交，页面正常刷新，但库里多了一条 `(15, '', '测试内容', …)`
- **真根因**：`title: str` 里 **`""` 是合法的 `str`** → Pydantic 挑不出毛病
- **验证**：读库看 `repr`
- **修**：`Field(min_length=1)` → 空字符串返回 **422**，且**函数体根本不会执行**（`INSERT` 跑不到）
- **教训**：**静默最可怕的不是"不报错"，是"它把脏数据写进了你的库"**

### #7 发帖失败，页面毫无反应

- **现象**：后端 422，但用户什么都看不到
- **真根因**：**`fetch` 不因 4xx 报错**（只在网络不通时 reject）→ 前端若无其事地继续刷新列表
- **验证**：服务端日志里 `POST → 422` 紧跟着 `GET /passage → 200` —— **那个 GET 就是"静默"的证据链**
- **修**：`if (!response.ok) { alert(err.detail[0].msg) }`，**先 `await response.json()` 把响应体读出来**
- **教训**：`return "错误信息"` **不等于"说出来"** —— `return` 是把值交回调用者（这里是 `onclick`，它不接、直接扔掉）

### #8 `.gitignore` 没生效 / `@object`

- **现象 A**：`.gitignore` 写了但 `mini-blog.db` 还在待提交列表里
- **真根因 A**：**`.gitignore` 里写了 `.gitignore` 自己**，而漏了 `*.db`
  - 常见误会：以为 `.gitignore` 里的内容是"要排除的清单"，其实那个列表是"git 现在看到的东西"
- **验证**：`git status --short --ignored` —— `??` = 未跟踪，`!!` = **已被忽略**
- **修**：只写 `__pycache__/` 和 `*.db`；**`.gitignore` 自己必须提交**（它是规则文件，别人 clone 也要用）
- **现象 B**：`alert(response)` 弹出 `[object Object]`
- **真根因**：把**整个对象**塞进"要文字的位置"，JS 会先"变形"，对象的默认变形结果就是 `[object Object]`
  - 同一机制：`j + "|"` 把数组变形为 `"8,a,b"`（Day 1 也踩过）
- **修**：一路挖到那一格 —— `err.detail[0].msg`

### #9 push 报 `src refspec main does not match any`

- **真根因**：本地分支叫 `master`，推的是 `main` → 本地**没有叫 main 的分支**
- **验证**：`git branch` 列出来只有 `master`
- **修**：`git branch -M main`（**必须在第一次 commit 之后**，否则报 `no commit on branch`）

### #10 注册接口说"成功"，库里 0 条

- **现象**：`/user_register` 返回 `{"message":"注册成功"}`，但 `SELECT * FROM user` 是空的
- **真根因**：`INSERT` 之后**漏了 `db.commit()`**。SQLite 的连接默认不开自动提交，`execute` 只是把语句放进事务，不 commit 就等于没写
- **验证**：接口返回 200 **不能当证据**，判据只能是库里 `COUNT(*)`
- **教训**：**"接口说成功" ≠ "数据进去了"** —— 静默家族第 N 张脸

### #11 注册能过、登录 422，因为一个收 JSON 一个收表单

- **现象**：注册用 `json={"username":...}` 能过；登录同样写法返回 422
- **真根因**：登录用的是 `OAuth2PasswordRequestForm`，它要的是 **`application/x-www-form-urlencoded` 表单**，不是 JSON
- **修**：登录用 `data={"username":..., "password":...}` + `headers={"content-type": "application/x-www-form-urlencoded"}`
- **教训**：**同一个项目里两种请求体格式可以共存** —— 写测试前先看后端要什么，别假设

### #12 `err.detail[0].msg` 在 401 上炸成 `undefined`

- **现象**：密码错时弹窗显示 `undefined`
- **真根因**：**`detail` 的类型随状态码变**：422 的 `detail` 是**数组**（`[{"msg":...}]`），404 / 401 的 `detail` 是**字符串**（`"用户或密码错误"`）。`"字符串"[0].msg` → `undefined`
- **修**：分型处理
  ```javascript
  const msg = Array.isArray(err.detail) ? err.detail[0].msg : err.detail;
  ```
- **教训**：**同一个字段，在不同分支里是不同类型** —— 报错信息本身也要先判断形状

### #13 `secret` 只有 13 字节

- **现象**：`InsecureKeyLengthWarning: The HMAC key is 13 bytes long, which is below the minimum recommended length of 32 bytes for SHA256`
- **真根因**：`secret="my_now_secret"`（`main.py:20`）随手起的，长度不够
- **修**：部署周改成环境变量 + 32 字节以上随机串
- **教训**：**警告不是装饰** —— 它说的是"这个密钥可被暴力猜出"，而密钥泄露 = 任何人能伪造 token

### #14 `ModuleNotFoundError: No module named 'main'`

- **现象**：`pytest` 跑测试，`conftest.py` 第一行就炸
- **真根因**：直接敲 `pytest` 时，`sys.path` 里**没有项目根**，只有参数所在目录
- **修**：`python -m pytest test -v` —— `-m` 会让 Python 把**当前目录**加进 `sys.path`
- **教训**：**"命令能不能跑"取决于它怎么被启动的**，和代码无关。详见 §9.2

### #15 `sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread`

- **现象**：内存库在 `conftest.py` 建好，测试一跑就报跨线程
- **真根因**：`TestClient` 在**另一个线程**里执行请求，SQLite 连接默认绑创建它的线程
- **修**：`sqlite3.connect(":memory:", check_same_thread=False)`
- **教训**：**"同一个进程"不等于"同一个线程"** —— 单线程写的代码进测试框架就会暴露

### #16 测试全绿，但一个用例都没跑

- **现象**：`pytest` 输出 `passed`，改坏代码也不红
- **真根因（三种，都踩过）**：
  1. 断言写成 `r.status_code == 401`，**没写 `assert`** → 表达式算完就扔
  2. 函数名不叫 `test_*` → **根本不被收集**
  3. `headers={"Authoriazation": ...}` **拼错** → 服务端收不到头 → 报 `Not authenticated`，把"头没发出去"伪装成"token 无效"
- **验证**：**故意改坏一处，看它红不红**。不红就是假绿
- **教训**：**「全绿」有四种可能** —— 真对 / 没执行 / 断言写错 / 断言没写（§8.2 判据 4 的测试版）

### #17 `setdefault` 写在 `import main` 之后，照样 `KeyError`

- **现象**：`conftest.py` 里明明写了 `os.environ.setdefault("MINI_BLOG_SECRET", ...)`，`pytest` 还是崩在 `main.py:21` 的 `KeyError: 'MINI_BLOG_SECRET'`
- **根因**：`import` 是**立即执行**。`from main import app, get_db` 在 `conftest.py:4`，而 `setdefault` 在 `conftest.py:7` —— 走到第 4 行时 `main.py` 全文已经跑完，第 21 行当场抛异常，第 7 行永远没机会执行
- **修法**：把 `import os` 和 `setdefault` 提到**所有 `import main` 之前**（现在是 `conftest.py:1-2`）
- **教训**：**给模块铺环境变量的代码，必须写在 import 那个模块之前。** 模块顶层代码在被 import 的那一刻就执行，不是等调用函数时

### #18 设置环境变量兜底值，等于没改

- **现象**：把 `secret="my_now_secret"` 改成 `secret=os.environ.get("MINI_BLOG_SECRET", "5f3a9c1e...")`，测试全绿，grep 也搜不到旧密钥 —— 看起来改完了
- **根因**：`.get(键, 默认值)` 在键缺失时**静默返回默认值**。那个 64 位字面量还在源码里，部署时忘设环境变量它照样生效 —— 危害和原来的硬编码**一模一样**，只是更隐蔽
- **验证（可用同样的手法自查）**：把这个字面量当密钥去 `jwt.encode({"username":"admin_owner",...})`，能成功签出 token 并解回来 —— 说明任何读到源码的人都能伪造任意身份（`get_current_user` 只验签名不查库）
- **修法**：`secret=os.environ["MINI_BLOG_SECRET"]` —— 没有就抛 `KeyError`，让配置缺失**在启动时暴露**，而不是在生产被人利用时暴露
- **教训**：`os.environ.get(键, 字面量)` 是**假修复**。要么用 `os.environ[键]`（缺了就崩），要么在 `conftest.py` 里 `setdefault`（测试自供电）

### 4.10 排查方法论（比具体修法更值钱）

| 原则 | 具体做法 |
|---|---|
| **报错分两头看** | 5xx：浏览器只报"坏了"，**原因在服务端终端的 traceback**。读 traceback 只看两处：**指向自己文件的那一条** + **最后一行** |
| **判据要放数据源** | 库里 `repr` > 浏览器页面 > 终端 |
| **偶发问题 → 放大成必现** | 加 `time.sleep(2)` 把并发顺序问题从毫秒放大到 2 秒，一眼看清 |
| **确认"生效了吗"不能靠猜** | git 用 `--ignored`；`row_factory` 打印 `type(...)`；改 HTML 要 `Ctrl+Shift+R` |
| **"没报错"有四种可能** | 代码真对 / 有错没人执行 / **你根本没在看那个页面** / 报错被筛掉 |

---

## 5. 待办与后续计划

### 5.1 已完成（2026-10-18 ~ 10-31）

| 事项 | 状态 |
|---|---|
| 写 `README.md` 并 push | ✅ commit `e8f0018` |
| 两数之和哈希版 | ✅ 0ms / 100%，两处卡点（`seen` 位置、查 `target - nums[m]`）都修好 |
| 加登录（注册 + 登录 + JWT 鉴权） | ✅ `d9c7415` / `a5cdb09` |
| `author` 字段 | ✅ 启动时 `ALTER TABLE` 迁移，旧数据 NULL，前端兜底“佚名” |
| 补测试（pytest） | ✅ `19d060c` / `b63f125` / `703edf9` / `9bc627e`，**12 个用例全绿**，见 §9 |
| `host` 改 `0.0.0.0` | ✅ `b75de79` |
| **技术债清理（Day 21）** | ✅ secret 进环境变量 / `requirements.txt` 补 `bcrypt`+`PyJWT` 修行尾 / 注册重名 404→409 / 补 `GET /passage` 与 author 落库两个测试 |
| LeetCode 206 反转链表 | ✅ 手写通过（迭代版，`prev`/`curr` 三行核心） |

### 5.2 下周（部署周 Day 22-25）

| 事项 | 说明 |
|---|---|
| ~~技术债清理~~ | ✅ 2026-10-31 已还清，见 §5.1 |
| **服务器** | 复用旧机或买新的（学生机）；能 SSH 上去为准 |
| **装环境传代码** | Python + 依赖 + `git clone`；`.db` 不传，靠启动自建 |
| **systemd 守护** | 服务挂了自动拉起；开机自启 |
| **两个待定** | ①服务器复用还是新买 ②端口是否仍用 8000 |

### 5.3 更远

| 事项 | 说明 |
|---|---|
| **真分页**（`LIMIT` / `OFFSET`） | 文章多了必须有 |
| **编辑 / 删除** | 补全 CRUD |
| **搜索** | 顺带练 `LIKE` / 索引 |
| **CSS** | 现在完全没有样式 |
| **榨干 SQLite** | 索引 / `EXPLAIN QUERY PLAN` / 窗口函数 / FTS5，之后再谈 PostgreSQL（寒假） |
| **补缺的测试** | 空库 `[]`、hashpassword≠明文、GET 无 token 401、bcrypt 72 字节上限、分页（见 §9.6） |
| **AI 摘要功能** | 给每篇文章生成摘要，2 天量级 |
| **旧坑复习机制** | 每天重写一道前天做过的题 |
| **把旧博客也上 GitHub** | ⚠️ 先做 §6.2 的三件事 |

---

## 6. 风险与约束

### 6.1 技术债（按危害排序）

| 债 | 危害 | 怎么还 |
|---|---|---|
| ~~`secret="my_now_secret"`（`main.py:20`）硬编码，13 字节~~ | ~~密钥进 Git = 任何人都能伪造 token~~ | ✅ 已还 2026-10-31：改 `os.environ["MINI_BLOG_SECRET"]`（`main.py:21`），测试靠 `conftest.py:2` 的 `setdefault` 供电。**生产必须自己设环境变量，不设就启动即崩** |
| ~~`host="127.0.0.1"`~~ | ~~部署后外部访问不到~~ | ✅ 已改 `0.0.0.0`（`main.py:103`） |
| ~~完全没有认证~~ | ~~任何人能发帖~~ | ✅ 已加 JWT 鉴权，`/passage` 与 `/passage_add` 都要 token |
| ~~`requirements.txt` 是 CR-only 行尾~~ | ~~pip 能读但 GitHub 显示异常~~ | ✅ 已还 2026-10-31：重写为 LF 行尾，无空行空格 |
| ~~零测试~~ | ~~改一处不知道崩没崩~~ | ✅ 已还 2026-10-30：10 个用例，见 §9。2026-10-31 补到 12 个 |
| ~~`requirements.txt` 未写 `bcrypt` / `pyjwt`~~ | ~~换机器 `pip install -r` 装不全，登录直接 ImportError~~ | ✅ 已还 2026-10-31：补 `bcrypt==4.0.1` / `PyJWT==2.13.0`，`pip --dry-run` 四行全 satisfied |
| ~~注册接口重复用户名返回 404~~ | ~~语义应为 409 Conflict~~ | ✅ 已还 2026-10-31：`main.py:80` 改 409，`test_register.py:20` 同步；`frontend/register.html` 不用改（只看 `response.ok`） |
| **测试依赖没进 `requirements-dev.txt`** | 换机器能跑服务但跑不了 `pytest`（缺 `pytest` / `httpx`） | 新建 `requirements-dev.txt`，写 `pytest==9.1.1` / `httpx==0.28.1` |
| **`add_passage()` 里变量名还是 `list1` / `list2`** | 与 `id="title"` / `id="content"` 不一致，读代码费劲 | 改名 |
| **日期格式 `2026-10-14 17-04-21`** | 用 `-` 当时间分隔符，不是标准格式，排序/解析都别扭 | 改 `%H:%M:%S` |
| ~~无 `author` 字段~~ | ~~分不清谁发的~~ | ✅ 已加 `author` 列（启动时 `PRAGMA table_info` 判断后 `ALTER TABLE`），旧数据为 NULL，前端 `??= "佚名"` 兜底 |
| **`get_current_user` 只验签名，不查用户是否存在** | 知道密钥就能伪造任意用户名（含不存在的） | 解出 `username` 后查一次 `user` 表，不存在则 401 |
| **测试用的密钥字面量仍在 `conftest.py:2`** | 这个值进了 Git。只影响测试环境（生产靠真环境变量），但读者容易误以为它是生产密钥 | 在 `conftest.py` 注释里写明「仅测试用」，或改成 `secrets.token_hex(32)` 每次随机生成 |

### 6.2 安全（**动 GitHub 之前必看**）

- **当前 mini-blog 里没有密钥、没有密码、没有用户数据** → 公开仓库是安全的 ✅
- ⚠️ **旧博客（`D:\博客代码\`）不能直接公开**：
  1. `user.db` 里有 **`user` 表**（账号 + 密码哈希）
  2. `main.py` 里 **`SECRET` 是硬编码的**（25 字节）
- **判据（每次 push 前都问一句）**：**这个文件里有没有不该公开的东西？**
  - GitHub 的 Public 仓库 = 全世界永久可访问，**推错一次，删了也会被缓存和爬走**

### 6.3 环境约束（本机特有，换机器会踩）

| 事实 | 影响 |
|---|---|
| 终端是 **Windows PowerShell 5.1** | `curl` 是 `Invoke-WebRequest` 的别名，网上抄的 curl 命令会报错；**传中文必须带 `charset=utf-8`** |
| Python 在 `D:\code\python\python.exe` | 不是 `python` 命令，要用绝对路径 |
| VSCode 主程序被改名成 `new_Code.exe` | 命令行是 `new_code .`，不是 `code .` |
| **`.py` 双击 = 运行**（文件关联到 `py.exe`） | 想编辑要点右键 → 打开方式 |
| Git Bash 的 `/tmp` 与原生 python.exe 不互通 | 临时文件中转要用 Windows 路径 |

### 6.4 学习节奏约束（**这是最重要的约束**）

这个项目本质是**训练**，不是产品。所以有几条规则不能破：

| 规则 | 说明 |
|---|---|
| **不看旧代码** | 不许翻 `D:\博客代码\`，那是作弊 |
| **允许查文档** | 代码里 `# LOOKUP:<网址>` 标记的就是查过的地方 |
| **不直接给答案** | 教学顺序：**复现现象 → 让作者先猜 → 亲手跑 → 沉淀原理 → 作者自己改** |
| **没跑过的代码不 review** | "改了"不算数，跑出来的输出才算 |
| **每天 ≈ 2 小时** | 作者是大二在读，这是课余时间。**不要按全职排期** |
| **求助券 5 张** | 每天问 AI 的机会有限，逼自己先查 |

> 接手者如果是 AI：**先讲清一个概念再让它动手；不要替它写代码；每次布置改动都要它回报输出。**

---

## 7. 接手第一天操作手册

### 7.1 把项目跑起来

```powershell
cd D:\mini-blog
D:\code\python\python.exe -m uvicorn main:app --reload
```

浏览器开 `http://127.0.0.1:8000/` —— **没 token 会自动跳到 `/login.html`**，先注册再登录，之后能看到文章列表 + 发帖框。

> ⚠️ 现在 `host="0.0.0.0"`，本地和局域网都能访问；本机仍用 `127.0.0.1:8000`。

### 7.2 确认它真的在工作（四条命令）

```powershell
# ① 跑测试（最快确认后端逻辑没崩）
D:\code\python\python.exe -m pytest test -v
#    预期：12 passed

# ② 接口通不通（要带 token，否则 401 是正常的）
curl.exe -s http://127.0.0.1:8000/passage

# ③ 库里几条
D:\code\python\python.exe -c "import sqlite3;c=sqlite3.connect('mini-blog.db');print(c.execute('SELECT COUNT(*) FROM passage').fetchone()[0])"

# ④ 端口谁在占（服务起不来的第一诊断）
netstat -ano | Select-String ':8000'
```

> ⚠️ **服务启动前必须先设 `MINI_BLOG_SECRET`**，否则 `main.py:21` 直接 `KeyError: 'MINI_BLOG_SECRET'` 起不来：
> `$env:MINI_BLOG_SECRET="这里放 32 字节以上的随机串"`

### 7.3 改完怎么确认生效（**最容易出错的地方**）

| 改了什么 | 怎么生效 | 常见误判 |
|---|---|---|
| `.py` | 重启服务（`--reload` 会自动） | 只看终端 banner —— **banner 只在 bind 那一刻打印** |
| `.html` / `.js` | **在浏览器里重新加载页面**（建议 `Ctrl+Shift+R`） | **改了文件 ≠ 改了正在跑的那个页面** |
| `conftest.py` / `test/*.py` | 立即生效，重跑 pytest 即可 | 测试文件改名后仍看旧报告 —— pytest 有缓存，加 `--cache-clear` |
| `.gitignore` | 立即生效 | 用 `git status --short --ignored` 确认（`??` / `!!`） |
| 数据库加字段 | **必须重启服务**（迁移在模块级，启动时跑一次） | 只 `--reload` 改了别的文件，以为迁移也跑了 |

### 7.4 Git 日常四步

```bash
git status                        # 我改了啥
git add .                         # 放进篮子
git commit -m "说清这次做了什么"    # 真正存下来
git push                          # 推到 GitHub（已用 -u 绑过，不用写后面那串）
```

**判据：好的 commit 只做一件事** —— 别把"加登录 + 改样式 + 修 bug"混成一笔。

**当前仓库状态（2026-10-18 实测）**：
```
461c4e8 初始版本：文章列表 + 发布功能
## main...origin/main          ← 本地与远程一致（无 ahead/behind）
```
分支 `main`，远程 `origin` = `https://github.com/useoopz/mini-blog.git`（公开）。

---

## 8. 附录：概念速查

### 8.1 「静默」家族 —— 十张脸，一条主线

```
IF NOT EXISTS 白干              row_factory 设了等于没设
'123abc' → 0                    name="list" 写成 id
Latin-1 编中文 → ?              createElement("lili") 造出没人认识的标签
conent-type 拼错                textcontent 小写 c
fetch 吞 404/422                HTML 空标签被浏览器默默修正
```

**统一判据：「不报错」从来不是「没问题」。**

- ⭐ **跨语言差异**：写错属性名 → **Python 报 `AttributeError`；JS 不报错，原地给你造一个新属性**
  ⇒ **JS 里"没报错也没效果"，第一件事查大小写**

### 8.2 四条通用判据

| # | 判据 | 用在哪 |
|---|---|---|
| 1 | **判据要选在"对和错会给出不同结果"的地方** | 自测设计（1 条数据分不出循环位置；两个终端输出必然一样） |
| 2 | **"准备好了" ≠ "发生了"** | `def f()` 没调用 / 拿了变量没用 / 造了元素没挂 / 改了文件没 commit |
| 3 | **"位置决定结果"** | 路由顺序、`row_factory` 与 `cursor`、`createElement` 在不在循环里 |
| 4 | **"没报错"有四种可能** | 代码真对 / 有错没人执行 / **没在看那个页面** / 报错被筛掉 |

### 8.3 异步三格（Promise）

```
fetch(url)        → 拿一张「凭据」（Promise）
await             → 去取货（Response，还没拆）
.json()           → 拆箱（又是一张凭据）
await             → 真数据
```

**判据**：**`await` 前面的代码保证已发生；`await` 后面的代码可能还没发生。**
想"读库变了之后的列表"，就必须写在 `await` 之后。

---

## 9. pytest 测试体系（2026-10-26 ~ 10-31 建立）

> 当前状态（2026-10-31 实测）：`test/` 下五个文件（`test_register.py` / `test_login.py` / `test_auth.py` / `test_passage.py` / `test_author_name.py`）+ 根目录 `conftest.py`，**12 个用例全绿**，`2.27s`。
> 命令：`D:\code\python\python.exe -m pytest test -v`

### 9.1 文件怎么组织
| 规则 | 内容 |
|---|---|
| 目录 | 测试放 `test/`，`conftest.py` 放**项目根**（不是 `test/` 里） |
| 文件名 | 必须 `test_*.py`，否则 pytest 不收集 |
| 函数名 | 必须 `test_*`，**漏了就静默不执行** —— 报了“全绿”，其实一个都没跑 |
| 为什么不能随便放 | 测试文件要能 `import main`。`pytest` 直接跑时只把**参数所在目录**加进 `sys.path`，`test/` 下就 `ModuleNotFoundError: No module named 'main'` |

### 9.2 跑测试的命令

```powershell
# 全量（日常用这个）
D:\code\python\python.exe -m pytest test -v

# 只看某个文件 / 某类用例
D:\code\python\python.exe -m pytest test/test_auth.py -v
D:\code\python\python.exe -m pytest test -k "register" -v

# 想看 print 输出时加 -s
D:\code\python\python.exe -m pytest test -v -s
```

**为什么必须 `python -m pytest` 而不能直接 `pytest`**：

- `python -m xxx` 会让 Python 把**当前工作目录**放进 `sys.path[0]`
- 直接敲 `pytest` 时，`sys.path` 里没有项目根 → `conftest.py` 里的 `from main import app, get_db` 直接炸
- 这就是那次 `ModuleNotFoundError: No module named 'main'` 的根因，不是文件放错了

**排查口诀**：`import` 报错 → 先看是不是用了 `pytest` 而不是 `python -m pytest`。

### 9.3 `conftest.py` 里有什么

四个 fixture + 一段全局替换 + 一行环境变量，`conftest.py` 共 50 行：

| fixture / 语句 | 干什么 | 依赖谁 |
|---|---|---|
| `os.environ.setdefault(...)`（**第 2 行，必须在 import main 之前**） | 给测试进程注入一个假密钥，让 `main.py:21` 的 `os.environ["MINI_BLOG_SECRET"]` 有值 | 无 |
| `override_get_db` + `app.dependency_overrides`（24-26 行） | 把真库换成内存库 | 无 |
| `clear`（`autouse=True`，27-32 行） | 每个用例前后清空两张表 | 无（自动跑） |
| `client`（33-35 行） | 返回 `TestClient(app)`，一个“假浏览器” | 无 |
| `user`（36-43 行） | 用随机用户名注册一个账号，返回 `(name, password)` | `client` |
| `token`（44-50 行） | 用 `user` 的账密登录，返回 `access_token` 字符串 | `client`, `user` |

> ⚠️ **第 1-2 行的顺序是硬约束**：`import main` 在第 6 行，而 `main.py:21` 一被 import 就执行 `os.environ["MINI_BLOG_SECRET"]`。`setdefault` 放到第 6 行之后 → `KeyError`（§4-#17）。

**fixture 链怎么串**：`token` 依赖 `user`，`user` 依赖 `client`。测试函数只要写 `def test_x(client, token)`，pytest 会**自动按依赖顺序**先把 `client` 准备好，再 `user`，再 `token` —— 不需要手写调用顺序，这是 fixture 最核心的机制。

**为什么用户名要随机**：`f"u_{uuid.uuid4().hex[:8]}"`。因为 `user` 表在同一个进程里共享，固定名字会在第二个用例撞“用户名已存在”。

### 9.4 测试隔离的两层（**别混成一句**）

```
第 1 层：内存库  → 隔离「测试」和「生产数据」
第 2 层：clear   → 隔离「测试」和「测试」
```

**第 1 层 —— 不污染真实库**

```python
conn = sqlite3.connect(":memory:", check_same_thread=False)
def override_get_db():
    yield conn
app.dependency_overrides[get_db] = override_get_db
```

- `:memory:` = 库只活在内存里，进程结束就消失，`mini-blog.db` 一个字节都不动
- **生命周期跟着“连接”走**：这条 `conn` 在模块级创建，所以是**整个测试进程共用一份**；一旦 `close()` 或进程退出，库和数据全没
- 常见坑：建完表把连接 `close()` 了，再新建一条连接 → `no such table`（**新连接是另一张空库**）
- `check_same_thread=False`：`TestClient` 在**另一个线程**里跑请求，SQLite 默认禁止跨线程用同一连接，不加就报
  `sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread.`
- `app.dependency_overrides[get_db] = override_get_db`：FastAPI 的依赖注入替换点。`main.py` 里每个路由写的是 `Depends(get_db)`，这里把它换成“给内存库”，**业务代码一行都不用改**

**第 2 层 —— 用例之间不串数据**

```python
@pytest.fixture(autouse=True)
def clear():
    conn.execute("DELETE FROM user")
    conn.execute("DELETE FROM passage")
    conn.commit()
    yield
```

- 因为内存库是**进程级共享**，上一个用例注册的用户会留到下一个用例 → 必须清
- `autouse=True`：不用在测试函数参数里写 `clear`，每个用例自动跑

### 9.5 「测试说谎」清单（最值钱的一节）

**核心判据：「测试全绿」不等于「代码对」。绿有四种可能 —— 真对 / 没执行 / 断言写错 / 断言没写。**

| 症状 | 真根因 | 判据 |
|---|---|---|
| 永久绿，改坏代码也不红 | `r.status_code == 401` 写了比较但**没写 `assert`** | 故意改坏一处，看它红不红 |
| 某个用例从不出现 | 函数名不以 `test_` 开头，或文件名不对 → **根本没被收集** | 数一下 `-v` 输出的用例数，和文件里写的一致吗 |
| 报 `Not authenticated`，以为是 token 问题 | `headers={"Authoriazation": ...}` **拼错** → 服务端收不到头 → 走了“无 token”分支 | 报错信息和预期不符时，先检查**头名**，别急着怀疑 token |
| 连接失败 / 404 | URL 少开头的 `/` | 打印实际请求 URL |
| 测试名和内容对不上 | `test_register_duplicate` 里测的是短密码 | 一个用例只证明一件事，名字必须说出它证明什么 |
| 该红的地方不红 | 断言太弱（只断 `status_code`，不断 `detail` 文案） | 一个用例至少断两样：状态码 + 关键字段 |

### 9.6 现有 12 个用例覆盖了什么

| 文件 | 用例 | 证明什么 |
|---|---|---|
| `test_register.py` | 4 个 | 注册成功 / 用户名重复（409） / 密码太短 / 用户名太短 |
| `test_login.py` | 3 个 | 登录成功 / 密码错误 / 用户不存在（后两者都返 401，防用户名枚举） |
| `test_auth.py` | 3 个 | 无 token → `Not authenticated` / 假 token → `token无效或已过期` / 真 token → 200 发布成功 |
| `test_passage.py` | 1 个 | 带 token 请求 `GET /passage` → 200 且 body 是 `list` |
| `test_author_name.py` | 1 个 | 用某用户 token 发帖后，读回来的那条 `author` 等于该用户名 |

**还缺的**：
1. bcrypt 72 字节上限（超长密码应返 422 而不是 500）
2. `/passage` 空库时返回 `[]`（不是 `None`、不是 500）
3. 注册后 `hashpassword` 列**不等于**明文密码（防止哪天有人把哈希改回明文）
4. `GET /passage` 无 token → 401（鉴权覆盖到读接口，目前只测了写接口）
5. 分页参数（等 `/passage` 支持 `page` 之后）

### 9.7 变异测试：怎么证明你的测试真的在干活

改坏一行代码，看测试会不会红。**红 = 有效；还是绿 = 这个断言是摆设。**

2026-10-31 实测案例：

| 改动 | 结果 | 说明 |
|---|---|---|
| `main.py:70` 的 `current_user` 改成 `"HACKED"` | `AssertionError: assert 'HACKED' == 'u_2383bedc'`，**1 failed** | `test_author_name.py:14` 的 author 断言有效 |
| 改回来 | 12 passed | 回到基线，确认改动可逆 |

**做法**：`Copy-Item main.py main.py.bak` → 改一处 → 跑 `pytest` → `Move-Item main.py.bak main.py -Force`。**改完必须恢复并重跑，确认回到全绿**，否则你会把一个坏改动留在工作区。

---

*本文档由 `.workbuddy/memory/` 的项目记忆整理而成，所有数字（版本号、提交号、条数、字节数）均来自磁盘实测，非回忆。*
