# 换机器跑起来 / 部署记录

这份文件只解决一件事：**把项目搬到另一台机器（或服务器）上，怎么让它跑起来。**

不写完整运维手册。只写每次都会忘、忘了就卡住的几步。

---

## 一、换机器要做的事（按顺序，别跳）

### 1. 拿代码

```bash
git clone https://github.com/useoopz/mini-blog.git
cd mini-blog
```

克隆下来**没有** `mini-blog.db` —— 它在 `.gitignore` 里。数据库靠启动时 `CREATE TABLE IF NOT EXISTS` 自建空表。**这是设计，不是缺文件。**

### 2. 装依赖

```bash
pip install -r requirements.txt
```

装四个包：`fastapi` / `uvicorn` / `bcrypt` / `PyJWT`。

> 要跑测试还得另外装：`pip install pytest httpx`（这两个还没进任何 requirements 文件，属于待还的技术债）。

### 3. 设环境变量（**最容易忘的一步**）

`main.py:21` 是：

```python
secret = os.environ["MINI_BLOG_SECRET"]
```

**没设这个变量，启动直接 `KeyError: 'MINI_BLOG_SECRET'` 退出。** 这是故意的 —— 配置缺失应该在启动时立刻暴露，而不是留一个默认值在生产里悄悄生效。

### 4. 启动

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

本地开发加 `--reload`；服务器上**不要加**（它会监视文件变化，浪费资源，且生产不该自动重载）。

### 5. 确认它真的在工作

```bash
python -m pytest test -v          # 预期 12 passed
curl -s http://127.0.0.1:8000/passage   # 预期 401 Not authenticated —— 这是对的，说明服务活着且鉴权生效
```

---

## 二、`MINI_BLOG_SECRET` 从哪来

### 生成一个随机串

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

输出 64 个十六进制字符（字符串长度 64 字节，对应 32 字节随机熵）。JWT 用 HS256 签名，密钥字符串短于 32 字节会触发 `InsecureKeyLengthWarning`（之前用 13 字节的 `my_now_secret` 就撞过这个警告）。

验证长度：`python -c "import secrets; s=secrets.token_hex(32); print(len(s.encode()), 'bytes')"` → 输出 `64 bytes`。

**每台机器用不同的串。** 不要把这个串提交进 Git。

### Windows PowerShell（临时，关窗口就失效）

```powershell
$env:MINI_BLOG_SECRET="生成的那个串"
python -m uvicorn main:app --reload
```

### Linux（临时，当前 shell 有效）

```bash
export MINI_BLOG_SECRET="生成的那个串"
python -m uvicorn main:app --reload
```

### Linux（永久，systemd 用这个）

写进 systemd 的 service 文件，而不是 `.bashrc`：

```ini
[Service]
Environment="MINI_BLOG_SECRET=生成的那个串"
```

原因：systemd 启动的进程不读 `.bashrc`，环境变量必须写在 unit 文件里（或用 `EnvironmentFile=`）。

### 检查设上了没有

```bash
# PowerShell
if ($env:MINI_BLOG_SECRET) { "已设置，长度 $($env:MINI_BLOG_SECRET.Length)" } else { "没设" }

# bash
echo ${#MINI_BLOG_SECRET}    # 输出 0 就是没设
```

> ⚠️ **不要把密钥写进 `main.py` 的默认值里**，比如 `os.environ.get("MINI_BLOG_SECRET", "5f3a...")` —— 那等于没改：密钥照样进 Git，而且忘设变量时它静默生效，比硬编码更隐蔽。这个坑踩过一次，见 `HANDOVER.md` §4-#18。

---

## 三、还没做但迟早要做的（每次部署前看一遍）

| 事项 | 为什么 |
|---|---|
| `uvicorn` 挂 systemd | 服务崩了自动拉起、开机自启；现在手动跑，SSH 一断就停 |
| 端口放行 | 云服务器要在安全组里开对应端口，否则外网访问不到 |
| HTTPS | 现在全是明文 HTTP，密码和 token 裸奔。需要 Nginx/Caddy 反代 + 证书 |
| 数据库备份 | `mini-blog.db` 是单文件，挂了就全没。定时 `cp` 到别处 |
| `pytest` / `httpx` 进 `requirements-dev.txt` | 换机器能跑服务但跑不了测试 |
