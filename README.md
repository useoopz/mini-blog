# mini-blog

一个**从零手写**的迷你博客：注册 / 登录 / 发帖 / 看文章。
FastAPI + SQLite + 原生 JS，**无前端框架、无 ORM、无脚手架**。

## 快速开始

### 1. 装依赖

```bash
pip install -r requirements.txt
```

### 2. 设密钥（**必须，否则启动即崩**）

`main.py:21` 是 `secret=os.environ["MINI_BLOG_SECRET"]` —— 没设这个环境变量会直接 `KeyError` 退出。这是故意的：配置缺失要在启动时暴露，而不是留一个默认值悄悄生效。

生成一个 32 字节以上的随机串：

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

然后设进环境变量：

```powershell
# Windows PowerShell（当前窗口有效）
$env:MINI_BLOG_SECRET="把上面生成的串粘这里"
```

```bash
# Linux / macOS（当前 shell 有效）
export MINI_BLOG_SECRET="把上面生成的串粘这里"
```

### 3. 启动

```bash
python -m uvicorn main:app --reload
```

打开 <http://127.0.0.1:8000/> 。没 token 会自动跳到 `/login.html`，先注册再登录。

## 接口

四个业务接口。**除注册和登录外都要带 token**。

| 方法 | 路径 | 请求体 | 鉴权 |
|---|---|---|---|
| POST | `/user_register` | **JSON** `{"username","password"}`（都 ≥3 字符） | 无 |
| POST | `/user_login` | **表单** `username=..&password=..` | 无 |
| GET | `/passage` | — | ✅ |
| POST | `/passage_add` | **JSON** `{"title","content"}` | ✅ |

> ⚠️ 注册收 JSON、登录收**表单**，这是 `OAuth2PasswordRequestForm` 的要求 —— 两者写法不同不是笔误。

### 走一遍完整流程

```bash
# ① 注册
curl -X POST http://127.0.0.1:8000/user_register \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"pass123"}'
# → {"message":"注册成功"}
#   用户名已存在时返回 409 {"detail":"用户名已存在"}

# ② 登录拿 token（注意是表单，不是 JSON）
curl -X POST http://127.0.0.1:8000/user_login \
  -d "username=demo&password=pass123"
# → {"message":"登陆成功","access_token":"eyJhbGciOi...","token_type":"bearer"}
#   密码错或用户不存在都是 401 {"detail":"用户名或密码错误"}（同一个回答，防用户名枚举）

# ③ 带着 token 发帖
curl -X POST http://127.0.0.1:8000/passage_add \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -d '{"title":"第一篇","content":"hello"}'
# → {"message":"发布成功"}
#   标题或正文为空时返回 422

# ④ 带着 token 读全部文章
curl -s http://127.0.0.1:8000/passage \
  -H "Authorization: Bearer eyJhbGciOi..."
# → [{"id":1,"title":"第一篇","content":"hello","date":"2026-11-01 15-22-06","author":"demo"}]
```

**不带 token 访问 `/passage`** 返回 `401 {"detail":"Not authenticated"}`；
**token 无效或过期**返回 `401 {"detail":"token无效或已过期"}` —— 这两种 401 是不同分支，排查时分清楚。

> **Windows PowerShell 5.1 注意**：`curl` 是 `Invoke-WebRequest` 的别名，必须写 `curl.exe`；`-d` 里带引号的 JSON 会被 PowerShell 吃掉引号（结果是 422 `json_invalid`），要用 `--%` 让 PowerShell 停止解析：
>
> ```powershell
> curl.exe --% -X POST http://127.0.0.1:8000/passage_add -H "Content-Type: application/json" -d "{\"title\":\"test\",\"content\":\"hello\"}"
> ```
>
> 含中文时更稳的做法：把 body 写成 **UTF-8 无 BOM** 文件，再 `--data-binary "@body.json"`。

## 测试

```bash
python -m pytest test -v      # 预期 12 passed
```

必须用 `python -m pytest` 而不是直接 `pytest` —— 前者会把当前目录放进 `sys.path`，否则 `conftest.py` 里的 `from main import app` 会 `ModuleNotFoundError`。

测试用**内存库**（`:memory:`）+ `dependency_overrides` 替换 `get_db`，不碰 `mini-blog.db`。

## 踩过的坑

### 一、`yield conn.close()` 导致对象没有 cursor 属性

- **现象**：接口报错，数据库对象上没有 `cursor` 这个属性
- **原因与修法**：`get_db()` 要产出的是 `conn` 本身，所以应该是 `yield conn`，请求处理完后从 `yield` 回来再 `conn.close()`

### 二、`row_factory` 设了却没生效，输出还是元组

- **现象**：返回的数据格式仍然是元组，不是要求的对象格式
- **原因与修法**：`row_factory` 必须写在创建 cursor **之前**。cursor 在创建那一刻就把当时的 `row_factory` 抄走了，之后再去设置对已存在的 cursor 无效

### 三、前端少了 `await`，拿到的不是真数据

- **现象**：函数输出和预期不一样，但代码看着没错
- **原因与修法**：`fetch` 前面要加 `await`，少这一步拿到的是凭据（Promise）而不是响应，后面再用就错了

更多细节见 [HANDOVER.md](HANDOVER.md)。
