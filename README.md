# Friend Recommend System（校园好友推荐）

基于 Vue 3 + Vite 前端与 Flask + SQLite 后端的校园社交推荐系统，支持 **PSI（隐私集合交集）加密** + **Big Five 性格建模** + **语义标签匹配** 的多维度隐私保护推荐。

## 技术栈

| 部分 | 技术 |
|------|------|
| 前端 | Vue 3、Vue Router、Pinia、Vite 6、Heroicons、TanStack Virtual |
| 后端 | Flask、Werkzeug（密码哈希）、NumPy（向量计算） |
| 数据库 | SQLite（`backend/database/database.db`） |
| 语义模型 | SentenceTransformer（多语言预训练模型） |

## 环境要求

- Python 3.10 及以上（推荐 3.11+）
- Node.js 18 及以上（与 Vite 6 兼容即可）

## 快速开始

### 1. 克隆仓库

```bash
git clone <你的仓库地址>
cd friend-recommend-system
```

### 2. 初始化 SQLite 数据库

在 **`backend`** 目录执行（会在 `backend/database/` 下创建目录与 `database.db`，并建表、必要时迁移旧结构）：

```bash
cd backend
python init_db.py
cd ..
```

### 3. 安装 Python 依赖

```bash
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate

pip install -r requirements.txt
```

### 4. 安装前端依赖

```bash
npm run frontend:install
```

### 5. 启动后端 API

在 **`backend`** 目录：

```bash
cd backend
python app.py
```

默认监听 **http://127.0.0.1:5000**。健康检查：GET [http://127.0.0.1:5000/health](http://127.0.0.1:5000/health)。

### 6. 启动前端（开发）

另开终端，在项目根目录：

```bash
npm run frontend:dev
```

浏览器访问 **http://localhost:5173**。开发模式下，`/api` 由 Vite 代理到 `http://127.0.0.1:5000`。

### 7. 可选：示例数据

- 小规模联调：`cd backend && python insert_test_data.py`
- 大规模随机用户（需已安装 `Faker`）：`cd backend && python seed_data.py`

### 8. PSI 演示

```bash
cd backend
python demo_psi.py
```

## 环境变量（可选）

| 变量 | 说明 | 默认 |
|------|------|------|
| `PORT` | Flask 监听端口 | `5000` |
| `FRONTEND_URL` | 前端地址，用于 CORS 与根路由提示 | `http://localhost:5173` |
| `FLASK_SECRET_KEY` | Flask session 密钥，**生产环境务必设置** | 内置占位字符串 |
| `SEMANTIC_MODEL_NAME` | SentenceTransformer 模型名称 | `paraphrase-multilingual-MiniLM-L12-v2` |
| `SEMANTIC_MATCH_THRESHOLD` | 语义匹配阈值（0-1） | `0.55` |

## 根目录 npm 脚本说明

- `npm run frontend:install` — 安装前端依赖
- `npm run frontend:dev` — 前端开发服务器
- `npm run frontend:build` — 前端生产构建
- `npm run frontend:preview` — 预览构建结果

## 核心功能

### PSI 隐私集合交集
- 基于 OKVS（Oblivious Key-Value Store）协议的轻量级 PSI 实现
- 支持好友交集、兴趣交集、技能交集的计算
- 哈希编码保护原始数据隐私

### Big Five 性格建模
- 5 维度人格向量：外向性、宜人性、尽责性、神经质、开放性
- 支持快速测试（每维 1-5 分）和完整问卷（10 题）
- 性格相似度与互补度混合计算

### 语义标签匹配
- 使用 SentenceTransformer 对兴趣/技能标签进行向量化
- 计算标签集合间的余弦相似度
- 支持多语言语义理解

### 三模式推荐
- **好友模式**：侧重好友圈与兴趣匹配（权重：好友 40%，兴趣 40%，性格 20%）
- **组队模式**：侧重技能互补（权重：技能 50%，性格 20%）
- **恋爱模式**：侧重兴趣与性格互补（权重：兴趣 50%，性格 30%）

### 隐私控制
- 用户可控制是否分享：兴趣、技能、好友关系、性格向量
- 非好友仅能查看基础信息与标签数量
- 好友可见完整兴趣技能列表

## 生产部署注意

- 将演示短信验证码（固定 `123456`）替换为真实短信服务并做限流
- 设置强随机 `FLASK_SECRET_KEY`
- 如需更精准的语义匹配，安装 SentenceTransformer：`pip install sentence-transformers`
- 前端构建：`npm run frontend:build`，静态资源在 `frontend/dist/`

## 文档

更详细的目录说明、接口与数据流见 **[项目结构与代码功能说明.md](./项目结构与代码功能说明.md)**。
