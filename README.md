# mini-blog

## 简介

这是一个能发帖、能看文章的个人博客，用 FastAPI 实现。项目用于练习前后端入门，检验自己脱离 AI 的动手能力，希望通过这种方式提高自己的能力。

## 运行

1. 先安装依赖：`pip install -r requirements.txt`
2. 启动：`python.exe -m uvicorn main:app --reload`
   （main.py 里也写了启动函数，直接运行 main.py 也能启动）
3. 打开 <http://127.0.0.1:8000/> 即可看到主页

## 接口

现在后端只有两个接口：一个读文章，一个增加文章。

### 读文章 `GET /passage`

```bash
curl -s http://127.0.0.1:8000/passage
```

返回对象列表：

```json
[{"id": 8, "title": "乙组中文正常", "content": "加了charset就好", "date": "2026-10-14 17-04-21"}]
```

### 增加文章 `POST /passage_add`

```bash
curl -X POST http://127.0.0.1:8000/passage_add \
  -H "Content-Type: application/json" \
  -d '{"title":"test","content":"hello"}'
```

成功返回：

```json
{"message":"发布成功"}
```

标题留空时会被后端拒绝，返回 422：

```json
{"detail":[{"type":"string_too_short","loc":["body","title"],"msg":"String should have at least 1 character","input":"","ctx":{"min_length":1}}]}
```

> **Windows PowerShell 5.1 注意**：`curl` 是 `Invoke-WebRequest` 的别名，必须写 `curl.exe`；`-d` 里带引号的 JSON 会被 PowerShell 吃掉引号，要用 `--%` 让 PowerShell 停止解析：
>
> ```powershell
> curl.exe --% -X POST http://127.0.0.1:8000/passage_add -H "Content-Type: application/json" -d "{\"title\":\"test\",\"content\":\"hello\"}"
> ```

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
