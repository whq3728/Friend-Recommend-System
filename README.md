Friend Recommend System（校园好友推荐）

基于 Vue 3 + Vite 前端与 Flask + SQLite 后端的校园社交推荐演示项目：支持账号/手机登录、个人资料与隐私偏好、PSI + Jaccard 多模式推荐、好友请求与私聊等能力。

技术栈

| 部分 | 技术 |
|------|------|
| 前端 | Vue 3、Vue Router、Pinia、Vite 6、Heroicons、TanStack Virtual |
| 后端 | Flask、Werkzeug（密码哈希）、NumPy（推荐计算） |
| 数据库 | SQLite，文件默认路径 `backend/database/database.db` |

环境要求

- Python 3.10 及以上（推荐 3.11+）
- Node.js 18 及以上（与 Vite 6 兼容即可）

快速开始

1. 克隆仓库

```bash
git clone <你的仓库地址>
cd friend-recommend-system
```

2. 初始化 SQLite 数据库

在 **`backend`** 目录执行（会在 `backend/database/` 下创建目录与 `database.db`，并建表、必要时迁移旧结构）：

```bash
cd backend
python init_db.py
cd ..
```

说明：若仅拉代码、尚未有库文件，必须先执行 `init_db.py`，否则 API 读写数据库会失败。

3. 安装 Python 依赖

在项目根目录执行：

```bash
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate

pip install -r requirements.txt
```
4. 安装前端依赖

```bash
npm run frontend:install
```

或：

```bash
cd frontend && npm install && cd ..
```

5. 启动后端 API

在 **`backend`** 目录：

```bash
cd backend
python app.py
```

默认监听 **http://127.0.0.1:5000**。健康检查：GET [http://127.0.0.1:5000/health](http://127.0.0.1:5000/health)。

6. 启动前端（开发）

另开终端，在项目根目录：

```bash
npm run frontend:dev
```

浏览器访问 **http://localhost:5173**。开发模式下，`/api` 由 Vite 代理到 `http://127.0.0.1:5000`（见 `frontend/vite.config.js`）。

7. 可选：示例数据

- 小规模联调：`cd backend && python insert_test_data.py`
- 大规模随机用户（需已安装 `Faker`）：`cd backend && python seed_data.py`

环境变量（可选）

| 变量 | 说明 | 默认 |
|------|------|------|
| `PORT` | Flask 监听端口 | `5000` |
| `FRONTEND_URL` | 前端地址，用于 CORS 与根路由提示 | `http://localhost:5173` |
| `FLASK_SECRET_KEY` | Flask session 密钥，**生产环境务必设置** | 内置占位字符串 |

在 Windows PowerShell 中示例：

```powershell
$env:FLASK_SECRET_KEY="请换成随机长字符串"
$env:PORT="5000"
cd backend; python app.py
```

生产部署注意

- 将演示短信验证码（固定 `123456`）替换为真实短信服务并做限流。
- 设置强随机 `FLASK_SECRET_KEY`，并视情况收紧 `backend/config.py` 中的 `CORS_ORIGINS`。
- 前端构建：`npm run frontend:build`，静态资源在 `frontend/dist/`；需由 Web 服务器或反向代理将 **`/api` 转发到 Flask**，或与前端同源部署，否则浏览器无法访问 API。

根目录 npm 脚本说明

`package.json` 提供对子项目的前缀调用（无需 `cd frontend`）：

- `npm run frontend:install` — 安装前端依赖  
- `npm run frontend:dev` — 前端开发服务器  
- `npm run frontend:build` — 前端生产构建  
- `npm run frontend:preview` — 预览构建结果（需同时启动 Flask；已配置与 dev 相同的 `/api` 代理）

文档

更细的目录说明、接口与数据流见 **[项目结构与代码功能说明.md](./项目结构与代码功能说明.md)**。

许可证

若开源发布，请在本仓库中补充所选许可证文件（如 `LICENSE`）。
