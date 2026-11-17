# mini-blog 项目交接文档

> **生成日期**：2026-11-17（上一版 2026-11-04）
> **资料来源**：`.workbuddy/memory/` 下的每日日志（`2026-10-24` ~ `2026-11-16`）、`路线.md`、`题单.md`、`work-rules.md`，以及磁盘实测（行数、提交号、用例数、库内容）
> **读者**：接手这个项目的人，或者隔一段时间回来的作者本人
> **读法**：赶时间只看 §0；接手第一天照 §7 做；改代码前先看 §4 和 §8；动测试看 §9

---

## 0. 30 秒速览

| 项 | 内容 |
|---|---|
| **是什么** | 一个从零手写的迷你博客：注册 / 登录 / 发帖 / 看列表 / 改 / 删。FastAPI + SQLite + 原生 JS，**无前端框架、无 ORM、无脚手架**（后端 7 个路由，前端 3 个页面） |
| **在哪** | `D:\mini-blog\`（本地）｜`https://github.com/useoopz/mini-blog`（公开） |
| **当前 HEAD** | `09a1355`，`## main...origin/main`（本地与远程一致） |
| **测试** | **35 个用例全绿**，`10.87s`（2026-11-17 实测） |
| **代码量** | `main.py` 176 行 · `frontend/` 三页 100+48+42 行 · `conftest.py` 55 行 · `test/` 十个文件 426 行 |
| **数据** | `passage` 14 条、`user` 16 条、索引 `idx_author`（本地库） |
| **已经有的** | JWT 鉴权（含查库校验）· bcrypt 密码哈希 · 分页 · 只看自己的文章 · 编辑/删除（403/404 分开）· 索引 · 结构化日志写文件 · 全局异常处理（客户端只收人话）· 抓外链标题 |
| **还没有的** | 前端没有编辑/改帖入口（接口有）· 没有 PATCH · 外链抓取没加超时和 SSRF 防御 · 没有 Dockerfile · nginx 装了没反代 · 没有 CI |
| **下一步** | 阶段 4：给 `fetch_title` 加超时（4.2）→ 接入发帖流程并降级（4.3）→ SSRF 防御（4.4）。完整清单见 `.workbuddy/memory/路线.md` |

**一分钟跑起来**：

```powershell
cd D:\mini-blog
$env:MINI_BLOG_SECRET="5f3a9c1e7b2d4a6f8c0e1d3b5a7f9c2e4d6b8a0f1c3e5d7a9b2c4e6f8a0d1b3c"
D:\code\python\python.exe -m uvicorn main:app --reload
# 浏览器打开 http://127.0.0.1:8000/
```

> 不设 `MINI_BLOG_SECRET` 会直接 `KeyError` 退出。这是故意的设计，见 §6.1。

---

## 1. 项目背景与目标

### 1.1 这是什么

一个可以发文章、看文章、改文章、删文章的极简博客。后端 7 个路由，前端 3 个页面。

技术上刻意保持"原始"：

- **不用框架** —— 没有 Vue/React，前端是手写 HTML + 原生 `fetch` + DOM API
- **不用 ORM** —— 直接 `sqlite3` 写 SQL
- **不用脚手架** —— 没有模板，文件是手建的空文件

### 1.2 为什么做它（这一点比代码重要）

这个项目**不是为了"做一个博客"**。

作者之前已经有一个功能更完整的博客（`D:\博客代码\`，13 个接口、登录、评论、两条线上线），**但那个是跟着 AI 一步步做出来的**。

`mini-blog` 的真实目的是：**证明"关掉 AI 也能独立做出东西"**。

所以它有一条贯穿始终的规则（见 §6.4），违反了项目就失去意义。

### 1.3 验收判据与达成情况

| 判据 | 状态 |
|---|---|
| 能跑起来 | ✅ |
| 每个文件能说出职责 | ✅（§3.5） |
| 报错能自己定位 | ✅（§4 的每条都是自己查出来的） |
| 测试能证明代码在干活 | ✅（§9.7 变异测试，三个洞全被抓到） |
| 别人能访问 | ✅（服务器 `121.40.191.38` + systemd，见 §5.2） |
| 坏了能查 | ✅（`app.log` + 全局异常处理，见 §3.2 ⑤⑥） |

---

## 2. 已完成的工作与关键决策

### 2.1 时间线

| 天 | 日期 | 做了什么 | 提交 |
|---|---|---|---|
| Day 1 | 10-12 | 骨架：`main.py` / `requirements.txt` / `index.html` | — |
| Day 2 | 10-13 | 接数据库：`mini-blog.db` + `passage` 表；`GET /passage` | — |
| Day 3 | 10-14 | 加"写"：`POST /passage_add`；文章第一次上屏 | — |
| Day 4 | 10-15 | 接口从"数组套数组"改成对象列表；地址去写死；发帖表单 | — |
| Day 5 | 10-16 | 反静默：后端会拒绝（422）、前端会说话 | — |
| Day 6 | 10-17 | 建 Git 仓库 + 上 GitHub；LeetCode 1 | `461c4e8` |
| Day 7 | 10-18 | 修完两数之和 + 217；curl 攻坚；写 README | `e8f0018` |
| Day 8-10 | 10-19 ~ 10-21 | 注册（bcrypt）/ 登录（表单 + JWT）/ 鉴权；`author` 字段迁移 | `27492da` `517fea0` `0c766f0` |
| Day 11-15 | 10-22 ~ 10-26 | 前端三页 + 门禁；算法刷到 20 题 | `d9c7415` `a5cdb09` |
| Day 16-20 | 10-27 ~ 10-30 | pytest 从零：内存库隔离、`dependency_overrides`、三个 fixture | `fb2caf6` `b63f125` `703edf9` `9bc627e` |
| Day 21 | 10-31 | 技术债清理：secret 进环境、补包、409、补测试 | `bf6e7de` |
| Day 22-25 | 11-01 ~ 11-04 | 部署到服务器 + systemd；分页（`LIMIT`/`OFFSET` + 前端按钮） | `23f461a` `411627e` `07d860f` `e73d213` `0a31018` |
| Day 26-28 | 11-05 ~ 11-07 | 补测试（72 字节上限、哈希、空库、无 token） | `d4ff7ed` |
| Day 29-30 | 11-08 ~ 11-09 | `DELETE`（四道关）+ 前端删除按钮；`get_current_user` 加查库校验 | `3f9b7ef` `00e9a9c` `87ec97d` |
| Day 31 | 11-10 | `GET /passage/mine` + 隔离测试 | `5ebd138` |
| Day 32 | 11-11 | `passage.author` 加索引 | `3392765` |
| Day 33 | 11-12 | logging 写文件 + 请求日志中间件 | `3d44af1` |
| Day 34 | 11-14 | 全局异常处理器（客户端只收 500 人话） | `7f3b2d5` |
| Day 35-36 | 11-15 ~ 11-16 | `POST` 返回 201；`PUT /passage/{id}` + 7 个测试 | `0ba9eb2` |
| Day 37 | 11-16 | `fetch_title`（httpx + re，失败降级） | `09a1355` |

> 算法线独立推进：11-17 为止 **35 题**（哈希 6 + 双指针 6 + 栈 5 + 链表 8 + 滑动窗口 1 + 树 10），下一题 113。题单在 `.workbuddy/memory/题单.md`。

### 2.2 关键决策（每条都有代价，不是"最佳实践"）

| 决策 | 结论 | 理由 | 代价 |
|---|---|---|---|
| 前端托管方式 | 后端 `mount("/")` 托管前端 | 前后端同源 → 不触发 CORS，也不用开第二个服务 | **`mount("/")` 必须在所有路由之后**，否则吞掉接口（§4-#1、§4-#27） |
| 数据库连接 | `get_db()` 每个请求新建一条，`yield` + `close` | 多人同时访问各拿各的，不抢同一份 | 每请求一点连接开销（SQLite 本地可忽略） |
| 读接口返回格式 | 对象列表 `[{"id":8,"title":…}]` | 前端能按名字取字段；靠位置取改表就错，而且不报错 | 多一步 `[dict(r) for r in rows]` |
| 写接口校验位置 | 校验放后端（`Field(min_length=1)`） | 前端的检查只是体验优化，任何人都能绕过网页直接 curl | 前端要单独再写一遍提示逻辑 |
| 前端渲染方式 | `createElement` + `textContent`，不用 `innerHTML` 拼字符串 | 要显示的是用户输入的内容，拼 HTML 会执行别人的代码（XSS） | 代码比 `innerHTML` 长 |
| 请求地址 | 根相对 `/passage` | 换端口、换域名、部署到服务器都自动跟随 | 无 |
| 数据库文件 | 不进 Git（`*.db`） | 二进制存不出差异、每发一帖就变；`CREATE TABLE IF NOT EXISTS` 能自建空库 | 克隆下来是空的 |
| 密钥 | `os.environ["MINI_BLOG_SECRET"]`，缺了就崩 | 配置缺失要在启动时暴露，而不是生产里被人利用时暴露（§4-#18） | 每台机器都要设一遍，忘设就起不来 |
| 日志出口 | 只写 `app.log`（`filename=`），不双出口 | 一个出口好查；屏幕上看不到是正常的（§4-#24） | 终端没有实时日志，要 `Get-Content -Wait` |
| 异常处理位置 | `@app.exception_handler(Exception)`，不是中间件里 `try/except` | 不动已写好的中间件、FastAPI 标准做法 | 抛异常时中间件那行 INFO 日志不出现（§4-#26） |
| 创建类接口状态码 | `POST` 返回 **201** | 数据库多了一条新记录 → 201；没多 → 200 | 三个测试的断言要跟着改（§4-#28） |
| 外链抓取 | 失败返回空串，不抛 | 抓不到标题不该妨碍发文章 | 静默失败，只能靠日志区分"没抓到"和"抓到了空" |

---

## 3. 代码结构与重要模块

### 3.1 目录

```
D:\mini-blog\
├── main.py                176 行 · 整个后端（配置 / 建表迁移 / 鉴权 / 7 个路由 / 静态托管 / 启动块）
├── requirements.txt         6 个包（见 §3.4）
├── conftest.py             55 行 · 测试夹具（内存库 + 6 个 fixture + 测试用 secret）
├── test/                 426 行 · 10 个文件 35 个用例（见 §9.6）
│   ├── test_register.py    66 行  7 个
│   ├── test_update.py      97 行  7 个
│   ├── test_token_forge.py 49 行  3 个
│   ├── test_delete.py      48 行  4 个
│   ├── test_single.py      44 行  1 个
│   ├── test_login.py       30 行  3 个
│   ├── test_log.py         29 行  1 个
│   ├── test_auth.py        25 行  4 个
│   ├── test_passage.py     24 行  4 个
│   └── test_author_name.py 14 行  1 个
├── verify.py               本地验证脚本：不起端口，用 TestClient 打 5 个请求
├── .gitignore              __pycache__/  *.db  post.json  .workbuddy/  app.log  *.log  + 三个实测脚本
├── mini-blog.db            SQLite 库（不进仓库，两张表 passage / user）
├── HANDOVER.md             本文档
├── README.md               面向陌生人的项目说明
├── DEPLOY.md               换机器 / 部署记录（160 行）
├── .workbuddy/memory/      项目记忆（进 gitignore，只在本机）
│   ├── 路线.md             主线唯一事实来源（含欠账清单）
│   ├── 题单.md             算法题单唯一事实来源
│   ├── work-rules.md       依赖红线（§6.4）
│   └── 2026-10-24.md …     每日日志
├── frontend/
│   ├── index.html         100 行 · 首页（门禁 + 列表 + 发帖 + 删除按钮）
│   ├── login.html          48 行 · 登录页
│   └── register.html       42 行 · 注册页
└── __pycache__/            Python 缓存（不进仓库）
```

### 3.2 `main.py` —— 一个文件装了十段东西（按行号顺序）

| 区段 | 行 | 干什么 | 关键点 |
|---|---|---|---|
| **① 导入** | 1-13 | FastAPI 组件、`sqlite3`、`bcrypt`、`jwt`、`logging`、`httpx`、`re` | `httpx` 是阶段 4 才进来的，**必须写进 `requirements.txt`**（§4-#31） |
| **② 抓标题** | 15-22 | `async def fetch_title(url)`：httpx 请求 → 正则抠 `<title>` → 失败返回 `""` | 现在是独立函数，**没有接进发帖流程**，也没加超时 |
| **③ 数据模型** | 25-37 | `AddPassage`（title/content 各 `min_length=1`）、`UserRegister`（username/password 各 `min_length=3` + 72 字节校验） | `AddPassage` 被发帖和改帖两处复用 |
| **④ 应用与横切关注点** | 38-51 | `app = FastAPI()` → 请求日志中间件（39-45）→ 全局异常处理器（46-49）→ `basicConfig` + `getLogger`（50-51） | **中间件和异常处理器写在 `log` 定义之前**，靠"函数体在请求时才执行"生效。这不是错，但读代码时容易误判 |
| **⑤ 配置与连接** | 52-53 | `secret=os.environ["MINI_BLOG_SECRET"]`、`oauth2_scheme` | 缺环境变量就崩，故意的 |
| **⑥ 一次性初始化** | 54-76 | 连库 → 建 `passage` / `user` 表 → `PRAGMA table_info` 检查 `author` 列 → 缺则 `ALTER TABLE` → **`CREATE INDEX IF NOT EXISTS idx_author`** → `close()` | 模块级，启动只跑一次。顺序有硬约束，见 §4-#29 |
| **⑦ 鉴权与工具** | 77-95 | `get_db()`（每请求新建连接）、`get_current_user()`（验签 + **查库**）、`hash_passaword()` | `get_current_user` 里那次 `SELECT username FROM user` 是 11-09 补的（§4-#25） |
| **⑧ 七个路由** | 96-172 | 见下表 | 全部在 `mount("/")` 之前 |
| **⑨ 静态托管** | 173 | `app.mount("/", StaticFiles(directory="frontend", html=True))` | **必须在所有路由之后** |
| **⑩ 启动块** | 174-176 | `uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)` | `0.0.0.0` 才能被外部访问 |

**路由清单（7 个）**

| 行 | 方法 | 路径 | 请求体 | 鉴权 | 成功返回 |
|---|---|---|---|---|---|
| 96 | GET | `/passage` | — | ✅ | 200 · `page` / `page_size` 分页的对象列表 |
| 104 | GET | `/passage/mine` | — | ✅ | 200 · 只要自己的文章 |
| 112 | POST | `/passage_add` | JSON `{title,content}` | ✅ | **201** `{"message":"发布成功"}` |
| 119 | POST | `/user_register` | JSON `{username,password}` | 无 | **201** `{"message":"注册成功"}` |
| 131 | POST | `/user_login` | **表单** `username=&password=` | 无 | 200 `{"message","access_token"}` |
| 146 | DELETE | `/passage/{passage_id}` | — | ✅ | 200 `{"message":"删除成功"}` |
| 158 | PUT | `/passage/{passage_id}` | JSON `{title,content}` | ✅ | 200 `{"msg":"更改成功"}` |

失败路径统一：422 字段校验（`detail` 是**数组**）· 401 身份 · 403 越权 · 404 不存在 · 409 用户名重复 · 500 服务器内部错误（`detail` 是**字符串**）。

> ⚠️ **注册收 JSON、登录收表单**，这是 `OAuth2PasswordRequestForm` 的要求，前端两页写法不同就是这个原因（§4-#11）。

> ⚠️ **`detail` 的类型随状态码变**：422 是数组 `[{"type","loc","msg","input"}]`，401/403/404/409/500 是字符串。前端写 `err.detail[0].msg` 在 401 上会拿到 `undefined`（§4-#12）。

### 3.3 三个读/写接口的细节

```
GET /passage
     db.row_factory = sqlite3.Row        ← 必须在 db.cursor() 之前
     SELECT * FROM passage LIMIT ? OFFSET ?
     参数：page: int = Query(1, ge=1)、page_size: int = Query(10, ge=1, le=100)
     → [dict(r) for r in rows]

GET /passage/mine
     SELECT * FROM passage WHERE author=? LIMIT ? OFFSET ?
     ← WHERE 必须在 LIMIT 之前（§4-#30）
     走 idx_author 索引：SEARCH passage USING INDEX idx_author (author=?)

POST /passage_add
     date 由服务端生成（time.strftime("%Y-%m-%d %H-%M-%S")）
     author = current_user（来自 token，不是请求体）
     INSERT → db.commit() → 201

PUT /passage/{passage_id}
     四道关，顺序不能换：鉴权(401) → 存在吗(404) → 是你的吗(403) → UPDATE+commit(200)
     ← 只改 title/content，date 不动
```

### 3.4 `requirements.txt` 与数据库

六个包，全部写了版本号：

```
fastapi==0.141.1        ← 写应用（路由、校验）
uvicorn==0.52.4         ← 真跑服务、守端口
bcrypt==4.0.1           ← 密码哈希
PyJWT==2.13.0           ← 签发/校验 token
python-multipart==0.0.32 ← 登录收表单必需（漏了启动即崩，§4-#19）
httpx==0.28.1           ← fetch_title 用；也是 fastapi.testclient 的依赖（§4-#31）
```

> `pytest` **没进任何 requirements 文件**。换机器能跑服务，跑不了测试。要补就建 `requirements-dev.txt`。

- `passage` 表：`id INTEGER PRIMARY KEY AUTOINCREMENT` / `title TEXT` / `content TEXT` / `date TEXT` / `author TEXT`
- `user` 表：`id INTEGER PRIMARY KEY AUTOINCREMENT` / `username TEXT` / `hashpassword TEXT`
  - ⚠️ `username` **没有 UNIQUE 约束**，重名判断靠代码里的 `SELECT ... WHERE username=?`；并发下有竞态
- 索引：`idx_author ON passage(author)`，`/passage/mine` 走它；`/passage` 仍是 `SCAN`
- `.db` 不进仓库，克隆后靠 `CREATE TABLE IF NOT EXISTS` 自建空表；**加字段不会自动生效**，靠启动时 `PRAGMA table_info` + `ALTER TABLE`

### 3.5 一句话职责

| 文件 | 职责 |
|---|---|
| `main.py` | 服务器收到请求后做什么：配日志和异常 → 建库建表建索引 → 定数据形状 → 验身份 → 收请求 → 查/写 → 回结果 |
| `frontend/index.html` | 首页：门禁（没 token 跳登录）+ 列表 + 发帖 + 删除 |
| `frontend/login.html` / `register.html` | 登录 / 注册表单，成功后把 token 存进 `localStorage` |
| `conftest.py` | 测试的假环境：内存库 + 假浏览器 + 现成账号 + 现成 token |
| `verify.py` | 不开服务，用 `TestClient` 把五个关键请求打一遍，看日志和状态码 |
| `requirements.txt` | 换台机器，靠它把环境装起来 |
| `mini-blog.db` | 数据存在哪 |

---

## 4. 遇到的问题及解决方式（**本节最有价值**）

每条按「现象 → 真根因 → 怎么验证 → 怎么修」记录。全部是真实踩过的。

### 4.0 索引

| # | 一句话 | 关键词 |
|---|---|---|
| 1 | 接口突然全 404 | `mount("/")` 顺序 |
| 2 | 中文进库变 `???` | PowerShell 编码 |
| 3 | `row_factory` 设了没用 | cursor 抄配置 |
| 4 | 写死 `127.0.0.1` | 浏览器的"本机" |
| 5 | 列表重复叠 | 没清空容器 |
| 6 | 空标题能发出去 | `""` 是合法 str |
| 7 | 发帖失败页面没反应 | fetch 不因 4xx 报错 |
| 8 | `.gitignore` 没生效 / `[object Object]` | 规则文件自己也要提交 / 对象变形 |
| 9 | push 报 `src refspec` | 分支名 |
| 10 | 注册说成功库里 0 条 | 漏 `commit` |
| 11 | 登录 422 | 表单 vs JSON |
| 12 | `detail[0].msg` 是 undefined | detail 类型随状态码变 |
| 13 | secret 只有 13 字节 | 密钥长度 |
| 14 | `No module named 'main'` | `python -m pytest` |
| 15 | SQLite 跨线程 | `check_same_thread` |
| 16 | 测试全绿但没跑 | 假绿三形态 |
| 17 | `setdefault` 写在 import 后 | 模块顶层立即执行 |
| 18 | 环境变量兜底值 = 假修复 | `.get(键, 字面量)` |
| 19 | 漏包本机测不出来 | 干净环境验证 |
| 20 | 安全组删规则 ≠ 关端口 | 那个「删除」删整条 |
| 21 | 网络不通三种 | 拒绝 vs 超时 |
| 22 | 分页参数少 `: int` | 字符串算出错 |
| 23 | 负数进 SQLite 不报错 | 数据库的"宽容解释" |
| 24 | 日志中文乱码 | 不写 `encoding="utf-8"` |
| 25 | `get_current_user` 只验签 | 伪造任意用户名 |
| 26 | 抛异常时日志最安静 | 中间件被跳过 |
| 27 | 新加路由返回 404 | `mount("/")` 吞掉 |
| 28 | 改 201 后三个测试变红 | 更新约定 ≠ 修 bug |
| 29 | 第二次启动崩 | `CREATE INDEX` 缺 `IF NOT EXISTS` |
| 30 | `WHERE ... LIMIT ... and author=?` 报错 | 子句顺序 |
| 31 | 换机器 import 就崩 | 隐式依赖 |
| 32 | `except ExceptionGroup` 抓不住网络错 | 异常不在同一条链上 |
| 33 | 复制粘贴改一半 | 旧名字还在 |

### #1 接口突然全 404，但代码看着没问题

- **现象**：加了路由却打不开，或者首页把接口吞了
- **真根因**：Starlette **先注册先匹配**。`mount("/")` 写在路由前面 → 它接管一切
- **验证**：`GET /passage_add` 返回 **404 而不是 405**，就是被 `mount("/")` 当成"找静态文件"了
- **修**：所有路由 → `mount("/")` 放最末（现在是 `main.py:173`）

### #2 中文进库变成 `???`

- **现象**：用 PowerShell 发帖，库里存的是 `'???'`；浏览器和终端也显示乱码
- **真根因**：**PowerShell 5.1 在请求没有 `charset` 时，上下行都默认 ISO-8859-1（Latin-1）**
  - 上行：中文编不了 → 每字替换成 `?` → **库里真的坏了**
  - 下行：服务器发 UTF-8，PS 按 Latin-1 解 → **只是显示坏，数据是好的**
- **验证**：**读库里的 `repr`**。关键证据：`'没有charset'` → 库里变成 `'??charset'` —— ASCII 活着，只有中文死了
- **修**：请求头带 `charset=utf-8`。PS 5.1 里更可靠的做法是写 UTF-8 无 BOM 文件再 `--data-binary "@body.json"`
- **教训**：**两个"乱码"长得一样，本质不同。判据要放数据源，不放屏幕。**

### #3 加了 `row_factory` 却没用，接口 500

- **现象**：`ValueError: dictionary update sequence element #0 has length 4; 2 is required`
- **真根因（两层）**：
  1. `dict(rows)` 把一堆行整个丢给 `dict()` —— 它要的是"一串键值对"
  2. **`cursor` 在创建那一刻就抄走了连接的 `row_factory`** → 之后设 `db.row_factory` 对已存在的 cursor 无效
- **验证**：
  ```python
  cur = c.cursor(); c.row_factory = sqlite3.Row   # 先建后设
  print(type(cur.fetchone()).__name__)            # → tuple（没生效）
  ```
- **修**：`db.row_factory = sqlite3.Row` 放 `db.cursor()` 之前；返回改 `[dict(r) for r in rows]`

### #4 前端写死 `http://127.0.0.1:8000`，换端口就空

- **真根因**：`127.0.0.1` 指的是"正在解析它的那台机器"。这行 `fetch` 是**访客的浏览器**在跑 → 它去找访客自己的电脑
- **修**：改成根相对 `"/passage"`

### #5 每次点提交，列表重复一遍（10 条、15 条…）

- **真根因**：`passage()` 只往里加，从不清空
- **验证**：刷新页面重复就消失 → 渲染层问题，不是库
- **修**：循环之前 `list.innerHTML = ""`
- **教训**：**判据 —— "这个函数被调第二次会怎样？"**

### #6 空标题能发出去，库里躺了一条没标题的记录

- **真根因**：`title: str` 里 `""` 是合法的 `str` → Pydantic 挑不出毛病
- **修**：`Field(min_length=1)` → 空字符串 422，**函数体根本不会执行**
- **教训**：静默最可怕的不是"不报错"，是"它把脏数据写进了你的库"

### #7 发帖失败，页面毫无反应

- **真根因**：`fetch` 不因 4xx 报错（只在网络不通时 reject）→ 前端若无其事地刷新列表
- **验证**：服务端日志 `POST → 422` 紧跟着 `GET /passage → 200` —— 那个 GET 就是证据链
- **修**：`if (!response.ok) { alert(...) }`，先 `await response.json()` 把响应体读出来

### #8 `.gitignore` 没生效 / `[object Object]`

- **现象 A**：写了 `.gitignore`，`mini-blog.db` 还在待提交列表
- **真根因 A**：里面写了 `.gitignore` 自己，却漏了 `*.db`。另有一次是 `"post.json" | Add-Content` 粘成 `*.dbpost.json`，两条规则一起失效
- **验证**：`git status --short --ignored` —— `??` 未跟踪，`!!` 已被忽略
- **现象 B**：`alert(response)` 弹 `[object Object]`
- **真根因 B**：把整个对象塞进"要文字的位置"，JS 会先变形
- **修**：一路挖到那一格 —— `err.detail[0].msg`

### #9 push 报 `src refspec main does not match any`

- **真根因**：本地分支叫 `master`，推的是 `main`
- **修**：`git branch -M main`（必须在第一次 commit 之后）

### #10 注册接口说"成功"，库里 0 条

- **真根因**：`INSERT` 之后漏了 `db.commit()`。SQLite 连接默认不开自动提交
- **验证**：接口返回 200 不能当证据，判据只能是库里 `COUNT(*)`
- **注**：同一个坑 11-15 又在 `PUT` 里踩了一次（§4-#28 之后），`test_update_commits` 就是为它写的

### #11 注册能过、登录 422，因为一个收 JSON 一个收表单

- **真根因**：`OAuth2PasswordRequestForm` 要 `application/x-www-form-urlencoded`，不是 JSON
- **修**：登录用 `data={...}` + 对应 `content-type`

### #12 `err.detail[0].msg` 在 401 上炸成 `undefined`

- **真根因**：`detail` 类型随状态码变 —— 422 是数组，401/404 是字符串
- **修**：`const msg = Array.isArray(err.detail) ? err.detail[0].msg : err.detail;`

### #13 `secret` 只有 13 字节

- **现象**：`InsecureKeyLengthWarning: The HMAC key is 13 bytes long…`
- **修**：环境变量 + 32 字节以上随机串
- **教训**：警告不是装饰 —— 它说的是"这个密钥可被暴力猜出"

### #14 `ModuleNotFoundError: No module named 'main'`

- **真根因**：直接敲 `pytest` 时 `sys.path` 里没有项目根
- **修**：`python -m pytest test -v`（`-m` 会把当前目录加进 `sys.path`）

### #15 SQLite 跨线程

- **真根因**：`TestClient` 在另一个线程执行请求，SQLite 连接默认绑创建它的线程
- **修**：`sqlite3.connect(":memory:", check_same_thread=False)`

### #16 测试全绿，但一个用例都没跑

- **三种形态**：①`r.status_code == 401` 写了比较但**没写 `assert`** ②函数名不叫 `test_*` → 不被收集 ③`headers={"Authoriazation": ...}` 拼错 → 服务端收不到头
- **验证**：故意改坏一处，看它红不红（§9.7）

### #17 `setdefault` 写在 `import main` 之后，照样 `KeyError`

- **真根因**：`import` 是立即执行。走到 `from main import ...` 时 `main.py` 全文已经跑完
- **修**：`import os` + `setdefault` 提到所有 `import main` 之前（`conftest.py:1-2`）
- **教训**：给模块铺环境变量的代码，必须写在 import 那个模块之前

### #18 设置环境变量兜底值，等于没改

- **真根因**：`os.environ.get(键, 默认值)` 在键缺失时静默返回默认值，那个字面量还在源码里
- **验证**：把字面量当密钥去 `jwt.encode({"username":"admin_owner",...})`，能签出 token —— 说明任何读到源码的人都能伪造身份
- **修**：`os.environ["MINI_BLOG_SECRET"]`，没有就 `KeyError`
- **教训**：`os.environ.get(键, 字面量)` 是假修复

### #19 `requirements.txt` 漏一个包，本机测试全绿也发现不了

- **真根因**：登录收表单，FastAPI 解析表单必须靠 `python-multipart`；本机早装了，所以测不出来
- **修**：补 `python-multipart==0.0.32`（`8ec016c`）
- **教训**：依赖清单的正确性只能在干净环境验证

### #20 安全组「删规则」≠「关端口」

- **现象**：逐条点删除，把 22 / 80 / 443 三条一起删了，SSH 当场断开
- **真根因**：那个「删除」删的是整条规则
- **修**：想限制某端口，点「编辑」把授权对象从 `0.0.0.0/0` 改成 `你的IP/32`
- **教训**：改安全组要「改」，不要「删了再加」

### #21 网络不通有三种，长得完全不一样

| 现象 | 典型延迟 | 含义 | 该查哪里 |
|---|---|---|---|
| 连上了 | 10-60ms | 通路 + 服务在监听 | 没问题 |
| `Connection refused` | ~2000ms | 通路通、安全组已放行，但没有进程监听 | 服务启没启、监听地址 |
| `timed out` | 6000ms+ | 包被静默丢弃，通常是安全组没放行 | 安全组入方向 |

2026-11-02 17:06 同机实测：`22 通13ms` / `80 积极拒绝2074ms` / `8000 积极拒绝2094ms` / `8001 超时7007ms`

### #22 分页参数少了 `: int`，不传参数正常、一传就 500

- **真根因**：`page=Query(default=1,ge=1)` 没有类型标注，FastAPI 拿到的 `"2"` 还是字符串 → `TypeError: Unable to apply constraint 'ge' to supplied value 2`
- **为什么 pytest 没抓住**：12 个用例全是裸 `client.get("/passage")`，一个都不传 page
- **教训**：加了参数就要为参数写测试
- **同一件事的另一个坑**：`LIMIT ?` 和 `OFFSET?` 之间少了空格，SQLite 把 `OFFSET?` 当独立标识符

### #23 负数进 SQLite 不报错，它会「贴心地」做别的

- **实测**：`LIMIT 5 OFFSET -5` → 返回前 5 条（当成 0）；`LIMIT -1` → 返回全部
- **结论**：输入校验必须放参数层（`Query(ge=1)`），数据库对非法值的宽容通常不是报错，而是给出错误的数据

### #24 日志里的中文全变乱码

- **现象**：`app.log` 里中文读不出来，`UnicodeDecodeError: 'utf-8' codec can't decode byte 0xb1 in position 7: invalid start byte`
- **真根因**：`basicConfig` 没写 `encoding` 时，Windows 用系统默认编码（本机 `locale.getpreferredencoding()` = `cp936`）写文件
- **验证**：直接读字节 —— `b'passage\xb1\xbb\xb7\xc3\xce\xca'`，按 GBK 解正常，按 UTF-8 解炸
- **修**：`logging.basicConfig(..., filename="app.log", encoding="utf-8")`
- **同族坑**：PowerShell 5.1 的 `Set-Content -Encoding UTF8` 会给文件加 BOM（`EF BB BF`），FastAPI 解析 JSON 时看到 BOM 报 `JSON decode error`。要无 BOM 就用 `[System.IO.File]::WriteAllText($p, $s, (New-Object System.Text.UTF8Encoding($false)))`
- **教训**：**"文件看起来正常"和"字节正确"是两件事**

### #25 `get_current_user` 只验签，不查库

- **现象**：11-08 实测，用已知的测试密钥签一个 `{"username":"admin_owner"}`，能通过全部鉴权，即使库里没有这个人
- **真根因**：签名只证明"这个 token 是我们发的"，不证明"这个人还在"
- **修**：解出 `username` 后查一次 `user` 表，不存在返回 401（`main.py:85-89`）
- **配套测试**：`test/test_token_forge.py` 3 个用例
- **教训**：**架构级的洞不属于哪个接口**，它属于鉴权函数

### #26 抛异常时日志最安静

- **现象**：给路由加一句 `raise ValueError(...)`，`/ok` 有日志、出错的请求**一行都没有**
- **真根因**：中间件里 `await call_next(request)` 直接把异常抛出去，后面的 `log.info` 和 `return response` 全被跳过
- **修**：`@app.exception_handler(Exception)`，里面 `log.exception(...)` + 返回干净的 500
- **验证三层**：客户端收 `{"detail":"服务器内部错误"}`（不含 `Traceback`、不含 `.py`）· `app.log` 有 ERROR 行 + 完整栈 · `pytest` 仍 35 passed（证明 401/403/404 没被误变成 500）
- **两个机制的分工**：中间件管正常请求（含 404），`exception_handler` 管抛异常的请求。**分工的判据是"这个失败之后请求还能不能继续"**

### #27 新加的路由返回 404

- **现象**：临时加 `@app.get("/boom")` 验证异常处理，请求返回 404
- **真根因**：`mount("/")` 接管了所有未匹配路径，它比后加的路由优先
- **修**：验证时用 `app.router.routes.insert(0, APIRoute("/boom", fn, methods=["GET"]))` 插到最前
- **教训**：**新增路由必须写在 `mount("/")` 之前**（§4-#1 的第二次踩）

### #28 改 201 之后三个测试变红 —— 这不是修 bug

- **现象**：给 `POST` 加 `status_code=201`，`test_auth.py:18` / `test_author_name.py:9` / `test_register.py:8` 三处 `assert == 200` 变红
- **性质**：代码本来是对的，**需求变了**，测试必须跟着变 —— 这叫**更新约定**
- **为什么必须分清**：想成"修 bug"的人，下次测试红就习惯性删断言
- **同批还踩了**：`PUT` 里 `content-?` 写成减号 → `OperationalError: near "-": syntax error`；漏 `db.commit()` → 当前连接看得到改动、重开连接就回滚
- **检查清单**：**改状态码/字段名/路径 → 先搜前端怎么判断**（三个页面都用 `response.ok`，200–299 都 true，所以 201 不破前端）

### #29 第二次启动就崩

- **现象**：`CREATE INDEX idx_author ON passage(author)` 第一次 `import main` 正常，第二次报 `sqlite3.OperationalError: index idx_author already exists`
- **影响**：服务从第二次启动起就起不来
- **修**：`CREATE INDEX IF NOT EXISTS ...`（`main.py:75`）
- **同族的顺序约束**：`CREATE INDEX` **必须在 `ALTER TABLE ADD COLUMN` 之后** —— 旧库没有 `author` 列时先建索引会报 `no such column: author`
- **对照**：建索引前后 `PRAGMA table_info` 都是 5 列，`sqlite_master` 多出一个 `index` 对象 —— **索引不是加列，是加并列对象**

### #30 `WHERE` 写在 `LIMIT` 后面

- **现象**：`SELECT * FROM passage LIMIT ? OFFSET ? and author=?` → `OperationalError: no such column: author`
- **真根因**：SQL 子句顺序固定是 `SELECT … FROM … WHERE … LIMIT … OFFSET`。SQLite 把 `? and author=?` 当成一个表达式，`author` 自然找不到
- **修**：`SELECT * FROM passage WHERE author=? LIMIT ? OFFSET ?`

### #31 换机器 `import` 就崩：隐式依赖

- **现象**：`fetch_title` 用了 `httpx`，本机跑得好好的
- **真根因**：本机的 `httpx 0.28.1` 是 `fastapi.testclient` 带进来的，**不在 `requirements.txt` 里**。干净机器 `pip install -r` 之后没有它
- **修**：`requirements.txt` 显式加 `httpx==0.28.1`
- **教训**：能 import 不等于声明了。判断方法：`pip install -r requirements.txt --dry-run`，或在空 venv 里真装一遍（§4-#19 同族）

### #32 `except ExceptionGroup` 抓不住网络错误

- **现象**：`fetch_title` 里写 `except ExceptionGroup`，请求一个不存在的地址时 `httpx.ConnectError: All connection attempts failed` 直接逃逸
- **真根因**：`ExceptionGroup` 是 Python 3.11 新增的、装"一次抛出的多个异常"的类型，**和普通异常是平级关系，不在继承链上**

  ```
  ConnectError → NetworkError → TransportError → RequestError → HTTPError → Exception → BaseException
  ```

  `ExceptionGroup` 不在这条链的任何位置
- **修**：`except Exception`（要精确就 `except httpx.HTTPError`）
- **教训**：**接异常前先问"这两个类是父子还是兄弟"**

### #33 复制粘贴改一半（同一个 bug 的第三次）

| 日期 | 现象 | 后果 |
|---|---|---|
| 11-09 | `cursor.executr(...)` | 方法不存在，直接报错（好事） |
| 11-12 | 复制 `walk` 成 `walk1`，4 处忘记改名 | `nums1` 恒空，**两棵相同的树也返回 False** |
| 11-15 | `content-?` 写成本该是 `content=?` | `near "-": syntax error` |

- **共同点**：改了主体，忘了附属引用
- **判据**：复制代码后第一件事搜旧名字（VSCode `Ctrl+F`）
- **为什么列进本文档**：前两次靠报错发现，第三次（`walk1`）**不报错只出错**，是这三者里最危险的形态

---

## 5. 待办与后续计划

主线唯一事实来源是 `.workbuddy/memory/路线.md`（含"欠账清单"表）。这里只摘要点。

### 5.1 已完成

| 事项 | 状态 |
|---|---|
| 阶段 0 地基（跑起来 / 分层 / Git） | ✅ |
| 阶段 1 堵洞（bcrypt / JWT / 查库校验 / 401·403·404·409 / mine / 索引 / 测试） | ✅ |
| 阶段 2 可观测（logging 写文件 + 请求中间件 + 全局异常） | ✅ 2026-11-14 |
| 阶段 3 REST 语义（`PUT` + 201） | ✅ 3.1 / 3.2；**3.3 PATCH 欠着** |
| 阶段 4 接外部世界 | 🔶 4.1 `fetch_title` 完成，4.2-4.4 未做 |
| 部署到服务器 + systemd | ✅ 11-03（`systemctl enable` 已执行，重启未实测） |

### 5.2 服务器现状（2026-11-03 状态）

| 项 | 内容 |
|---|---|
| 地址 | `121.40.191.38`（阿里云 Ubuntu 22.04 / 2核1.6G / 40G，到期 2027-01-13） |
| 代码位置 | `/home/bloguser/mini-blog` |
| 运行方式 | systemd，unit 在 `/etc/systemd/system/mini-blog.service` |
| 关键配置 | `User=bloguser` / `WorkingDirectory=/home/bloguser/mini-blog` / `ExecStart=venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000` / `EnvironmentFile=.env` / `Restart=always` / `WantedBy=multi-user.target` |
| 密钥 | 新生成的 64 hex，写在 `/home/bloguser/mini-blog/.env`，`chmod 600` |
| 已验证 | `kill` 进程后 5 秒自动拉起，curl 返回 401 |
| 未验证 | 整机重启后是否自动起（`systemctl enable` 已跑，没重启试过） |
| nginx | 装了但没配反代，占着 80 端口返回默认欢迎页。mini-blog 在 8000 上不受影响 |

> ⚠️ 旧密钥 `my_now_secret` 进过 Git 历史，等于已公开。服务器上用的是 11-03 新生成的，本地用 `conftest.py` 的测试串。

### 5.3 下一步（按顺序）

| 阶段 | 内容 | 天数 |
|---|---|---|
| **阶段 4** | 4.2 加超时 `timeout=5` → 4.3 接入发帖流程并降级 → 4.4 SSRF 防御（拒绝 `127.0.0.1` / `169.254.169.254` / 内网段） | 3-4 |
| 欠账 | 3.3 `PATCH`（阶段 4 结束后立刻补，最晚阶段 6 之前） | 1 |
| 阶段 5 | 10 万行造数、深分页实测、决定要不要改游标分页 | 2-3 |
| 阶段 6 | `Dockerfile`（`.env` 不进镜像）→ `docker build/run` → nginx 反代 → `systemctl enable` 重启实测 | 3-4 |
| 阶段 7 | GitHub Actions：push 自动跑 `pytest` + README badge | 2 |
| 更远 | 前端补编辑入口 · CSS · 搜索（`LIKE`/索引）· `requirements-dev.txt` · 寒假迁 PostgreSQL | — |

**明确不碰**：Redis / 消息队列 / 微服务拆分 · Java / Go 八股 · 第二个项目（阶段 5 之后再定）· 游戏模组 API（依赖外部不稳定服务）

---

## 6. 风险与约束

### 6.1 技术债（按危害排序）

| 债 | 危害 | 怎么还 |
|---|---|---|
| **`fetch_title` 没有超时** | 目标站点不响应时，请求会一直挂着（阶段 4.2 的靶子） | `httpx.AsyncClient(timeout=5)` |
| **`fetch_title` 可以打内网** | 用户传什么 URL 就请求什么 → SSRF。能打到 `127.0.0.1:8000` 和自己的管理接口，也能打云元数据 `169.254.169.254` | 阶段 4.4：解析后校验 IP 不在内网段，禁 `file://` `gopher://` |
| **`user.username` 没有 UNIQUE** | 并发注册同名会出两条 | `ALTER TABLE` 加唯一索引，或建表时就写 `UNIQUE` |
| **每请求新建 SQLite 连接** | 并发高时锁竞争；SQLite 本来就是单写 | 寒假迁 PostgreSQL 时一并解决（连接池） |
| **`main.py` 176 行一个文件** | 改一处要读全文；没有分层 | 阶段 6 之后再考虑拆 `routers/` `db.py` |
| **`hash_passaword` 拼错** | 全项目沿用（`main.py:92` 定义、`127` 调用） | 改名前先全局搜，两处一起改 |
| **日期格式 `2026-10-14 17-04-21`** | 用 `-` 当时间分隔符，排序/解析别扭 | 改 `%H:%M:%S`；顺带考虑加 `updated_at` |
| **`pytest` 没进 requirements** | 换机器能跑服务，跑不了测试 | 建 `requirements-dev.txt` |
| **`conftest.py:2` 有测试用密钥字面量** | 已进 Git。只影响测试环境（生产靠真环境变量），但容易被误当成生产密钥 | 注释写明"仅测试用"，或改 `secrets.token_hex(32)` 每次随机 |
| **前端没有编辑入口** | `PUT` 接口存在但页面点不到 | 首页加「编辑」按钮，复用发帖表单 |

### 6.2 安全（**动 GitHub 之前必看**）

- **mini-blog 里没有生产密钥、没有真实用户数据** → 公开仓库是安全的 ✅
- ⚠️ **旧博客（`D:\博客代码\`）不能直接公开**：
  1. `user.db` 里有 `user` 表（账号 + 密码哈希）
  2. `main.py` 里 `SECRET` 是硬编码的（25 字节）
- **判据（每次 push 前问一句）**：**这个文件里有没有不该公开的东西？**
  - GitHub 的 Public 仓库 = 全世界永久可访问，**推错一次，删了也会被缓存和爬走**
- 已公开过的历史值：`my_now_secret`（13 字节，已废弃）、`conftest.py:2` 的 64 hex（仅测试）

### 6.3 环境约束（本机特有，换机器会踩）

| 事实 | 影响 |
|---|---|
| 终端是 **Windows PowerShell 5.1**，`pwsh` 命令不存在 | `curl` 是 `Invoke-WebRequest` 的别名，必须写 `curl.exe`；`-d` 里的引号会被吃掉，可靠写法是 `curl.exe --% ...` 或写 UTF-8 无 BOM 文件 + `--data-binary "@body.json"` |
| Python 在 `D:\code\python\python.exe` | 不是 `python` 命令，要用绝对路径 |
| 控制台编码是 GBK（`cp936`） | 中文输出在终端会乱码。规律：**写文件再 `Get-Content -Encoding utf8` 读** |
| VSCode 主程序改名成 `new_Code.exe` | 命令行是 `new_code .` |
| `.py` 双击 = 运行 | 想编辑要点右键 → 打开方式 |
| 自动化脚本里 `git checkout -- 文件` 可能被安全策略拦 | 单文件恢复走 `git stash`，或先确认无实质改动再 `git add` |
| `python -c "…"` 里的引号嵌套容易坏 | 复杂脚本写成临时 `.py` 文件再跑 |
| push 时 stderr 的 `NativeCommandError` | 那是 git 往 stderr 写进度，**判据是 `x..y  main -> main` 那一行** |

### 6.4 学习节奏约束（**这是最重要的约束**）

这个项目本质是**训练**，不是产品。规则不能破：

| 规则 | 说明 |
|---|---|
| **不看旧代码** | 不许翻 `D:\博客代码\`，那是作弊 |
| **允许查文档** | 代码里 `# LOOKUP:<网址>` 标记的就是查过的地方 |
| **不直接给答案** | 教学顺序：**复现现象 → 让作者先猜 → 亲手跑 → 沉淀原理 → 作者自己改** |
| **框架语法骨架可以给，函数体内容作者自己填** | 给整段成品等于给答案 |
| **没跑过的代码不 review** | "改了"不算数，跑出来的输出才算 |
| **代码先自己跑** | 报错原文贴出来再讨论，不许把"检查自己代码"也交出去 |
| **测试一人一半** | 骨架 + 断言思路给，**断言值作者填** |
| **一天最多一张券** | 「直接帮我写完 / 剩下的你帮我跑完」一天只能用一次，用完当天日志记一笔 |
| **成果标清谁做的** | AI 做的东西不得记成作者的成果 |
| **每天 ≈ 2 小时** | 大二在读，课余时间。不要按全职排期 |
| **算法 30 分钟放最前** | 不许被主线挤掉 |

> 接手者如果是 AI：**先讲清一个概念再让它动手；不要替它写业务代码；每次布置改动都要它回报输出。**

---

## 7. 接手第一天操作手册

### 7.1 把项目跑起来

```powershell
cd D:\mini-blog
# 下面这串是 conftest.py:2 的测试用密钥，已进 Git，不是生产密钥
$env:MINI_BLOG_SECRET="5f3a9c1e7b2d4a6f8c0e1d3b5a7f9c2e4d6b8a0f1c3e5d7a9b2c4e6f8a0d1b3c"
D:\code\python\python.exe -m uvicorn main:app --reload
```

浏览器开 `http://127.0.0.1:8000/` —— **没 token 会自动跳到 `/login.html`**，先注册再登录，之后能看到文章列表 + 发帖框。

> `host="0.0.0.0"`，本地和局域网都能访问；本机仍用 `127.0.0.1:8000`。

### 7.2 确认它真的在工作（四条）

```powershell
# ① 跑测试（最快确认后端逻辑没崩）
D:\code\python\python.exe -m pytest test -q
#    预期：35 passed

# ② 不开服务验一遍接口（现代替 curl 的主力手段）
#    verify.py:9 自己会 setdefault 一个密钥，不用先设环境变量
D:\code\python\python.exe verify.py
#    预期：注册 201 / 登录 200 拿到 token / passage 200 / mine 200 / nope 404

# ③ 库里几条
D:\code\python\python.exe -c "import sqlite3;c=sqlite3.connect('mini-blog.db');print(c.execute('SELECT COUNT(*) FROM passage').fetchone()[0])"

# ④ 端口谁在占（服务起不来的第一诊断）
netstat -ano | Select-String ':8000'
```

> ⚠️ **服务启动前必须先设 `MINI_BLOG_SECRET`**，否则 `main.py:52` 直接 `KeyError` 起不来。

### 7.3 改完怎么确认生效（**最容易出错的地方**）

| 改了什么 | 怎么生效 | 常见误判 |
|---|---|---|
| `.py` | 重启服务（`--reload` 会自动） | 只看终端 banner —— banner 只在 bind 那一刻打印 |
| `.html` / `.js` | 浏览器重新加载（`Ctrl+Shift+R`） | 改了文件 ≠ 改了正在跑的那个页面 |
| `conftest.py` / `test/*.py` | 立即生效，重跑 pytest | pytest 有缓存，必要时加 `--cache-clear` |
| `.gitignore` | 立即生效 | 用 `git status --short --ignored` 确认 |
| 数据库加字段/加索引 | **必须重启服务**（迁移在模块级，启动时跑一次） | 只 `--reload` 改了别的文件，以为迁移也跑了 |

### 7.4 Git 日常四步

```powershell
git status                        # 我改了啥
git add <具体文件>                 # 放进篮子（别用 git add . 吞进垃圾）
git commit -m "说清这次做了什么"    # 真正存下来
git push                          # 推到 GitHub
```

**判据：好的 commit 只做一件事** —— 别把"加登录 + 改样式 + 修 bug"混成一笔。

当前仓库：分支 `main`，远程 `origin` = `https://github.com/useoopz/mini-blog.git`（公开），HEAD `09a1355`。

---

## 8. 附录：概念速查

### 8.1 「静默」家族 —— 十四张脸，一条主线

```
IF NOT EXISTS 漏写              相当于白干（第二次启动才崩）
CREATE INDEX 缺 IF NOT EXISTS   第一次正常，第二次起不来
row_factory 设了等于没设          cursor 抄配置
'123abc' → 0                    类型转换不报错
name="list" 写成 id              拿不到元素
Latin-1 编中文 → ?               库里真坏了
createElement("lili")            造出没人认识的标签
conent-type 拼错                 请求头没生效
textcontent 小写 c               JS 原地造新属性
fetch 吞 404/422                 前端若无其事
INSERT 后没 commit               接口说成功，库里 0 条
日志没写 encoding                中文变乱码，读的时候才发现
except ExceptionGroup            异常直接逃逸
复制粘贴改一半（walk1）          不报错，只出错
```

**统一判据：「不报错」从来不是「没问题」。**

- ⭐ **跨语言差异**：写错属性名 → **Python 报 `AttributeError`；JS 不报错，原地造一个新属性**
  ⇒ **JS 里"没报错也没效果"，第一件事查大小写**

### 8.2 五条通用判据

| # | 判据 | 用在哪 |
|---|---|---|
| 1 | **判据要选在"对和错会给出不同结果"的地方** | 自测设计（1 条数据分不出循环位置） |
| 2 | **"准备好了" ≠ "发生了"** | 定义了没调用 / 拿了变量没用 / 造了元素没挂 / 改了文件没 commit |
| 3 | **"位置决定结果"** | 路由顺序、`row_factory` 与 `cursor`、`CREATE INDEX` 与 `ALTER`、`WHERE` 与 `LIMIT` |
| 4 | **"没报错"有四种可能** | 代码真对 / 有错没人执行 / 没在看那个页面 / 报错被筛掉 |
| 5 | **要改别人的东西，先搜谁在依赖它** | 改状态码先搜前端 `response.ok`；删测试先想它在守哪行代码 |

### 8.3 异步三格（Promise）

```
fetch(url)        → 拿一张「凭据」（Promise）
await             → 去取货（Response，还没拆）
.json()           → 拆箱（又是一张凭据）
await             → 真数据
```

**判据**：`await` 前面的代码保证已发生；`await` 后面的代码可能还没发生。

Python 侧对照：`async def` 里的 `call_next(request)` 返回的是 coroutine，**不 `await` 就读不到 `status_code`**（报 `AttributeError: 'coroutine' object has no attribute 'status_code'`）。

### 8.4 异常三层

```
BaseException
 ├── SystemExit / KeyboardInterrupt / GeneratorExit   ← 不该被普通 except 接住
 └── Exception
      ├── HTTPException（我们自己抛的，FastAPI 会转成对应状态码）
      ├── httpx.ConnectError → NetworkError → TransportError → RequestError → HTTPError
      └── ...

ExceptionGroup（3.11 新增，装"一次抛出的多个异常"）—— 与上面平级，不在链上
```

**两处降级的分工**：

| 位置 | 角色 | 判据 |
|---|---|---|
| `@app.exception_handler(Exception)` | 最后一道防线 | 这个失败之后整个请求做不下去了 |
| `fetch_title` 里的 `try/except` | 就地降级 | 这件事失败了，主流程还能继续（抓不到标题照样发文章） |

**反例**：给发帖路由包 `except Exception: pass` → 数据库写失败也返回"发布成功"。假成功比 500 危险。

### 8.5 索引与分页

| 概念 | 一句话 |
|---|---|
| 索引是什么 | 把 `author` 排好序**另存一份**（只存 `author` + `rowid`），空间换时间。**不是加列**，是加并列对象 |
| 为什么快 | 二分。10 万行 ≈ 2^17，最多 17 步。实测 SCAN 100,000 次比较 vs SEARCH 16 次 |
| `SELECT *` 的代价 | 索引只给了 `rowid`，其它列要**回表**补 |
| 索引没有"用法" | SQLite 自己选。`WHERE author=?` 走；`WHERE UPPER(author)=?`（函数包裹）不走；`LIKE '%x%'` 不走 |
| 小表可能不用索引 | 14 行时计划写 `SCAN` 属正常，索引确实建成了 |
| `OFFSET` 为什么慢 | `LIMIT 10 OFFSET 199990` 要先把前 199990 行数过去。20 万行实测 3.110ms vs `WHERE id > ?` 0.032ms，97 倍 |
| KEYSET 的取舍 | 上下页都能做（`WHERE id < ? ORDER BY id DESC`），**做不到跳页** —— `OFFSET 55` 是纯算术，`id > ?` 的问号值只有上一页数据里才有 |
| 验优化没改结果 | `SELECT ... FROM passage NOT INDEXED WHERE author=?` 强制扫表，与走索引的结果逐条比对。数据库自带的对照实验，不用备份库 |

---

## 9. pytest 测试体系

> 当前状态（2026-11-17 实测）：`test/` 下十个文件，**35 个用例全绿，10.87s**。
> 命令：`D:\code\python\python.exe -m pytest test -q`

### 9.1 文件怎么组织

| 规则 | 内容 |
|---|---|
| 目录 | 测试放 `test/`，`conftest.py` 放**项目根**（不是 `test/` 里） |
| 文件名 | 必须 `test_*.py`，否则 pytest 不收集 |
| 函数名 | 必须 `test_*`，**漏了就静默不执行** —— 报了"全绿"，其实一个都没跑 |
| 为什么不能随便放 | 测试文件要能 `import main`。`pytest` 直接跑时只把**参数所在目录**加进 `sys.path` |

### 9.2 跑测试的命令

```powershell
D:\code\python\python.exe -m pytest test -v                 # 全量
D:\code\python\python.exe -m pytest test/test_auth.py -v     # 单文件
D:\code\python\python.exe -m pytest test -k "register" -v     # 按名字筛
D:\code\python\python.exe -m pytest test -v -s                # 看 print
```

**为什么必须 `python -m pytest`**：`-m` 会让 Python 把**当前工作目录**放进 `sys.path[0]`；直接敲 `pytest` 时那里没有项目根，`conftest.py` 的 `from main import app, get_db` 直接炸。

### 9.3 `conftest.py` 里有什么（六个 fixture）

| fixture / 语句 | 干什么 | 依赖谁 |
|---|---|---|
| `os.environ.setdefault(...)`（**第 2 行，必须在 import main 之前**） | 给测试进程注入假密钥 | 无 |
| `override_get_db` + `app.dependency_overrides`（24-26） | 把真库换成内存库 | 无 |
| `clear`（`autouse=True`，27-32） | 每个用例前后清空两张表 | 无（自动跑） |
| `conn_`（33-35） | 直接暴露内存连接，用来验证"到底 commit 没有" | 无 |
| `client`（38-40） | 返回 `TestClient(app)`，一个假浏览器 | 无 |
| `user`（41-48） | 随机用户名注册一个账号，返回 `(name, password)` | `client` |
| `token`（49-55） | 用 `user` 的账密登录，返回 `access_token` | `client`, `user` |

> ⚠️ **第 1-2 行的顺序是硬约束**：`import main` 在第 6 行，`main.py:52` 一被 import 就执行 `os.environ["MINI_BLOG_SECRET"]`（§4-#17）。

**fixture 链**：`token` 依赖 `user`，`user` 依赖 `client`。测试函数写 `def test_x(client, token)`，pytest 自动按依赖顺序准备。

**为什么用户名要随机**：`f"u_{uuid.uuid4().hex[:8]}"`。`user` 表在一个进程内共享，固定名字会在第二个用例撞"用户名已存在"。

### 9.4 测试隔离的两层（**别混成一句**）

```
第 1 层：内存库  → 隔离「测试」和「生产数据」
第 2 层：clear   → 隔离「测试」和「测试」
```

第 1 层要点：`sqlite3.connect(":memory:", check_same_thread=False)` + `app.dependency_overrides[get_db]`，业务代码一行不改。**`:memory:` 的生命周期跟着连接走** —— 一旦 `close()` 或进程退出，数据全没；建完表 `close()` 再新建连接会报 `no such table`（新连接是另一张空库）。

第 2 层要点：内存库是进程级共享，上一个用例注册的用户会留到下一个，必须 `autouse` 清表。

### 9.5 「测试说谎」清单

**核心判据：「测试全绿」不等于「代码对」。绿有四种可能 —— 真对 / 没执行 / 断言写错 / 断言没写。**

| 症状 | 真根因 | 判据 |
|---|---|---|
| 永久绿，改坏也不红 | `r.status_code == 401` 没写 `assert` | 故意改坏一处，看它红不红 |
| 某个用例从不出现 | 函数名不以 `test_` 开头 / 文件名不对 | 数 `-v` 输出的用例数与文件里写的一致吗 |
| 报 `Not authenticated` | `headers={"Authoriazation": ...}` 拼错 | 先检查**头名**，别急着怀疑 token |
| 该红的地方不红 | 断言太弱（只断 `status_code`） | 一个用例至少断两样：状态码 + 关键字段 |
| 断言全过但功能坏了 | 只断"成功"，**没断"失败时真的没改到"** | 每个失败分支补一句阴性断言 |

**三种 422 长一样但根因不同**（curl 攻坚时收集的）：

| 返回里的 `type` | 说明 | 什么时候出现 |
|---|---|---|
| `json_invalid` | body 不是合法 JSON | 引号被 shell 吃掉 |
| `json_invalid`（`input:{}`） | body 是空的 | 参数被拆散，什么都没发出去 |
| `string_too_short` | JSON 合法，字段值是空串 | 自己的 `min_length=1` 在干活 |

### 9.6 现有 35 个用例覆盖了什么

| 文件 | 用例 | 证明什么 |
|---|---|---|
| `test_register.py` | 7 | 注册成功 / 用户名重复（409）/ 密码太短 / 用户名太短 / 密码超 72 字节（422）/ 登录密码超 72 字节（422）/ 库里存的是哈希不是明文 |
| `test_update.py` | 7 | 改自己的成功 / `date` 不变 / 改别人的 403 且真没改 / 不存在的 404 / 无 token 401 / 空标题 422 / **真的 commit 了** |
| `test_token_forge.py` | 3 | 伪造不存在的用户名 → 401；伪造存在的用户 → 401；正常 token → 200 |
| `test_delete.py` | 4 | 删自己的（200 且列表里消失）/ 删别人的 403 **且真没删掉** / 删不存在 404 / 无 token 401 |
| `test_single.py` | 1 | 两个用户各发文章，`/passage/mine` 只看得到自己的 |
| `test_login.py` | 3 | 登录成功 / 密码错误 / 用户不存在（后两者都 401，防用户名枚举） |
| `test_log.py` | 1 | 抛异常时客户端收干净 500（不含 `Traceback` / `.py` / 异常类名） |
| `test_auth.py` | 4 | 无 token → `Not authenticated` / 假 token → `token无效或已过期` / 真 token 发布 201 / 无 token 读列表 401 |
| `test_passage.py` | 4 | 带 token → 200 且 body 是 `list` / 翻页不重叠 / `page=0` 422 / 空库返回 `[]` |
| `test_author_name.py` | 1 | 用某用户 token 发帖后，读回来那条 `author` 等于该用户名 |

**写法上值得学的两处**（`test_update.py`）：

1. 每个"成功"都**改完再 GET 比对**，不只断状态码
2. 每个"失败"都补**阴性断言**（403 后读库确认没被改、422 后确认标题还是原值）

### 9.7 变异测试：怎么证明测试真的在干活

改坏一行代码，看测试会不会红。**红 = 有效；还是绿 = 这个断言是摆设。**

2026-11-15 实测（`PUT` 接口）：

| 改动 | 被谁抓到 |
|---|---|
| 删掉 `db.commit()` | `test_update_commits` |
| 删掉 403 检查 | `test_update_other_passage`（`assert 200 == 403`） |
| 删掉 404 检查 | `test_update_not_exist`（`TypeError: 'NoneType' object is not subscriptable`） |

2026-10-31 实测（author 落库）：

| 改动 | 结果 |
|---|---|
| `current_user` 改成 `"HACKED"` | `AssertionError: assert 'HACKED' == 'u_...'`，1 failed |
| 改回来 | 全绿 |

**做法**：在副本目录里改（`Copy-Item -Recurse` 一份到 `_mut`），跑测试，然后删副本。**别在主工作区改**，改完忘了恢复会把坏代码留在那。

---

*本文档由 `.workbuddy/memory/` 的项目记忆整理而成。所有数字（行数、用例数、提交号、条数）均来自 2026-11-17 磁盘实测，非回忆。*
