# mini-blog 项目交接文档

> **生成日期**：2026-10-18
> **资料来源**：`.workbuddy/memory/` 下的 `MEMORY.md` 与 `2026-10-12 ~ 2026-10-17` 每日日志
> **读者**：接手这个项目的人（或隔一段时间回来的作者本人）
> **阅读建议**：赶时间只看 §0；接手第一天照 §7 做

---

## 0. 30 秒速览

| 项 | 内容 |
|---|---|
| **是什么** | 一个**从零手写**的迷你博客：文章列表 + 发帖。FastAPI + SQLite + 原生 JS，无框架 |
| **在哪** | `D:\mini-blog\`（本地）｜`https://github.com/useoopz/mini-blog`（公开） |
| **能跑什么** | 首页显示全部文章；填标题+正文点提交，写库并自动刷新列表；空标题被后端拒绝并弹提示 |
| **代码量** | `main.py` 47 行 / `frontend/index.html` 50 行 / `requirements.txt` 2 个包 |
| **当前状态** | 能跑、有版本控制、有 GitHub。**没有登录、没有分页、没有测试、没有 CSS** |
| **下一步** | 写 README → 加登录 → 补分页 |

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
├── main.py               47 行 · 整个后端
├── requirements.txt      2 个包（fastapi / uvicorn）
├── .gitignore            __pycache__/  *.db
├── mini-blog.db          SQLite 数据库（不进仓库，当前 7 条）
├── frontend/
│   └── index.html        50 行 · 整个前端（HTML + JS）
└── __pycache__/          Python 缓存（不进仓库）
```

### 3.2 `main.py` —— 一个文件装了四件事（**按执行顺序**）

| 区段 | 行 | 干什么 | 关键点 |
|---|---|---|---|
| **① 数据模型** | 7-9 | `class AddPassage(BaseModel)` 定义"发过来的数据该长什么样" | `title` / `content` 都带 `Field(min_length=1)` → **空字符串会被拒** |
| **② 一次性初始化** | 13-22 | 连库 → `CREATE TABLE IF NOT EXISTS` → `commit` → `close` | 这段在**模块级**，服务启动时**只跑一次** |
| **③ 连接工厂** | 23-26 | `get_db()`：每请求新建一条连接，`yield` 出去，用完 `close` | 用 `Depends(get_db)` 注入 |
| **④ 两个路由** | 27-41 | `GET /passage` 读全部；`POST /passage_add` 写一条 | 都放在 `mount("/")` **之前** |
| **⑤ 静态托管** | 43 | `mount("/", StaticFiles(directory="frontend", html=True))` | **必须在所有路由之后** |
| **⑥ 启动块** | 44-46 | `uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)` | ⚠️ 部署到服务器要改 `host="0.0.0.0"` |

**两个路由的细节**

```
GET  /passage
     db.row_factory = sqlite3.Row      ← ⚠️ 必须在 cursor = db.cursor() 之前
     cursor = db.cursor()
     rows = cursor.fetchall()
     return [dict(r) for r in rows]    ← 每行转字典，得到"对象列表"

POST /passage_add
     请求体：{"title": "...", "content": "..."}
     date 由服务端生成（time.strftime）
     INSERT INTO passage (title, content, date) VALUES (?,?,?)
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
  - 实际安装版本（2026-10-18 实测）：`fastapi 0.141.1` / `uvicorn 0.52.4` / **`pydantic 2.13.5`**
    （pydantic 由 fastapi 间接带入，**未显式写进 requirements** —— 一般够用，想严谨可以补上）
- `passage` 表：`id INTEGER PRIMARY KEY AUTOINCREMENT` / `title TEXT` / `content TEXT` / `date TEXT`
- 当前 7 条数据；`.db` 不进仓库，克隆后靠 `CREATE TABLE IF NOT EXISTS` 自建空表

### 3.5 一句话职责（原作者口述，已校对）

| 文件 | 职责 |
|---|---|
| `main.py` | 服务器收到请求后做什么：建库建表 → 定数据形状 → 收请求 → 查/写 → 回结果 |
| `frontend/index.html` | 浏览器里长什么样（输入框、按钮、列表）+ 做什么（读列表、发文章） |
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

### 5.1 立刻（半天内）

| 事项 | 为什么 |
|---|---|
| **写 `README.md`** | 面试官打开仓库第一眼。要写：项目是什么、怎么跑、技术栈、遇到的问题 |
| **`git add README.md && git commit && git push`** | 顺手把 Git 流程再走一遍 |

### 5.2 一周内

| 事项 | 说明 |
|---|---|
| **加登录** | 独立重建的最后一块。参考旧博客的做法（`URLSearchParams` + `localStorage`），但要**自己写** |
| **算法：把两数之和的哈希版写完** | 当前卡在"字典位置 + 查错对象"两个问题上（见下） |
| **每天 30 分钟算法** | 唯一"不过就出局"的门槛（笔试机考），**目前执行率最低的一项** |

> **两数之和的卡点（2026-10-17 收工时状态）**：已写出用户字典的思路，但
> ① `seen = {}` 写在循环里（每轮清空）② 查的是 `nums[m]` 而不是 `target - nums[m]`。
> 三个官方用例全返回 `None`。修法就这两处。

### 5.3 更远

| 事项 | 说明 |
|---|---|
| **真分页**（`LIMIT` / `OFFSET`） | 文章多了必须有 |
| **编辑 / 删除** | 补全 CRUD |
| **搜索** | 顺带练 `LIKE` / 索引 |
| **CSS** | 现在完全没有样式 |
| **补测试**（pytest） | 现在 0 个测试 |
| **把旧博客也上 GitHub** | ⚠️ 先做 §6.2 的三件事 |

---

## 6. 风险与约束

### 6.1 技术债（按危害排序）

| 债 | 危害 | 怎么还 |
|---|---|---|
| **`main.py:46` 写死 `host="127.0.0.1"`** | 部署到服务器后**外部访问不到**（只监听本机） | 部署时改 `0.0.0.0` |
| **完全没有认证** | **任何人**能访问 `/passage_add` 发帖；也没有"作者"概念 | 加登录 |
| **`requirements.txt` 是 CR-only 行尾** | pip **能正常读**（已验证），但 GitHub 上显示异常、部分工具会警告 | VSCode 右下角改成 CRLF/LF 存一次 |
| **零测试** | 改一处不知道崩没崩 | 补 pytest（旧博客有 20 个用例可参考写法） |
| **`add_passage()` 里变量名还是 `list1` / `list2`** | 与 `id="title"` / `id="content"` 不一致，读代码费劲 | 改名 |
| **日期格式 `2026-10-14 17-04-21`** | 用 `-` 当时间分隔符，不是标准格式，排序/解析都别扭 | 改 `%H:%M:%S` |
| **无 `author` 字段** | 分不清谁发的（等加登录一起解决） | — |

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

```bash
cd D:\mini-blog
D:\code\python\python.exe -m uvicorn main:app --reload
```

浏览器开 `http://127.0.0.1:8000/` —— 应该看到 7 条文章 + 两个输入框 + 提交按钮。

### 7.2 确认它真的在工作（三条命令）

```bash
# ① 接口返回对象列表吗（最外层应该是 [ 然后每个元素是 { ）
curl -s http://127.0.0.1:8000/passage

# ② 库里几条（该和页面上的条数一致）
D:\code\python\python.exe -c "import sqlite3;c=sqlite3.connect('mini-blog.db');print(c.execute('SELECT COUNT(*) FROM passage').fetchone()[0])"

# ③ 代码改了但没生效？先看端口和文件时间
netstat -ano | grep ':8000'
ls -l --time-style=+"%m-%d %H:%M" main.py frontend/index.html
```

### 7.3 改完怎么确认生效（**最容易出错的地方**）

| 改了什么 | 怎么生效 | 常见误判 |
|---|---|---|
| `.py` | 重启服务（`--reload` 会自动） | 只看终端 banner —— **banner 只在 bind 那一刻打印** |
| `.html` / `.js` | **在浏览器里重新加载页面**（建议 `Ctrl+Shift+R`） | **改了文件 ≠ 改了正在跑的那个页面** |
| `.gitignore` | 立即生效 | 用 `git status --short --ignored` 确认（`??` / `!!`） |

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

*本文档由 `.workbuddy/memory/` 的项目记忆整理而成，所有数字（版本号、提交号、条数、字节数）均来自磁盘实测，非回忆。*
