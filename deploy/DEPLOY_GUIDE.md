# JNU Link 阿里云部署指南

## 快速开始

### 1. 准备工作

在开始部署之前，你需要：

1. **购买阿里云 ECS 服务器**
   - 推荐配置：2核2G内存，系统选择 Ubuntu 22.04 LTS 或 CentOS 7+
   - 确保服务器可以访问公网

2. **域名（可选）**
   - 可以直接使用服务器IP访问
   - 如需域名，先在域名服务商添加 A 记录指向服务器IP

3. **配置阿里云安全组**
   - 登录阿里云控制台 → ECS → 安全组
   - 添加入方向规则：
     - 协议：TCP
     - 端口：80, 443, 22
     - 来源：0.0.0.0/0

### 2. 配置部署脚本

编辑 `deploy/deploy.sh`，修改以下配置：

```bash
SERVER_USER="root"           # 服务器用户名
SERVER_HOST="你的服务器IP"      # 替换为你的服务器IP
SERVER_PORT="22"             # SSH端口
```

### 3. 配置服务器环境变量

编辑 `deploy/.env.server`，填写实际值：

```bash
FLASK_SECRET_KEY=openssl rand -hex 32  # 生成随机密钥
ALIYUN_ACCESS_KEY_ID=你的AccessKey ID
ALIYUN_ACCESS_KEY_SECRET=你的AccessKey Secret
# ... 其他配置
```

### 4. 服务器环境准备

在服务器上执行以下命令安装必要软件：

**Ubuntu/Debian:**
```bash
# 更新系统
apt update && apt upgrade -y

# 安装 Nginx
apt install -y nginx

# 安装 Python 和 pip
apt install -y python3 python3-pip python3-venv

# 安装 Supervisor
apt install -y supervisor

# 创建网站目录
mkdir -p /var/www/jnu-link
chown -R www-data:www-data /var/www/jnu-link
```

**CentOS:**
```bash
yum update -y
yum install -y nginx python3 python3-pip supervisor
```

### 5. 执行部署

返回本地项目目录，执行部署脚本：

```bash
cd friend-recommend-system
chmod +x deploy/deploy.sh
./deploy/deploy.sh
```

脚本会自动：
- 构建前端
- 上传文件到服务器
- 安装后端依赖
- 配置 Nginx 和 Supervisor
- 重启服务

### 6. 验证部署

部署完成后，访问：

- 前端：`http://你的服务器IP`
- 后端API：`http://你的服务器IP/api/`
- 健康检查：`http://你的服务器IP/health`

## 常用命令

### 查看服务状态
```bash
supervisorctl status jnu-link-backend
```

### 重启后端
```bash
supervisorctl restart jnu-link-backend
```

### 查看日志
```bash
# 后端日志
tail -f /var/log/jnu-link/backend.log

# Nginx 日志
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### 更新代码
```bash
# 修改代码后，重新运行部署脚本
./deploy/deploy.sh
```

### 停止服务
```bash
supervisorctl stop jnu-link-backend
nginx -s stop
```

## SSL 证书配置（可选）

如需 HTTPS，配置 Let's Encrypt 免费证书：

```bash
# 安装 Certbot
apt install -y certbot python3-certbot-nginx

# 获取证书（需要域名）
certbot --nginx -d your-domain.com

# 自动续期
certbot renew --dry-run
```

## 常见问题

### 1. 部署脚本报错 "Permission denied"
```bash
# 服务器上设置权限
chmod 600 /etc/supervisor/supervisord.conf
chmod +x /deploy/deploy.sh
```

### 2. Nginx 502 Bad Gateway
- 检查后端是否启动：`supervisorctl status jnu-link-backend`
- 检查端口是否被占用：`lsof -i:5000`

### 3. 前端静态资源 404
```bash
# 检查文件是否存在
ls -la /var/www/jnu-link/dist/

# 重建软链接
ln -sf /var/www/jnu-link/dist /var/www/html/jnu-link
```

### 4. 数据库问题
- 首次部署需要初始化数据库
- SSH 到服务器执行：
```bash
cd /var/www/jnu-link/backend
python3 init_db.py
```

## 项目结构

```
/var/www/jnu-link/           # 服务器项目根目录
├── backend/                 # Flask 后端
│   ├── app.py               # 应用入口
│   ├── config.py            # 配置文件
│   ├── .env                 # 环境变量（需手动创建）
│   ├── database/           # 数据库目录
│   │   └── database.db     # SQLite 数据库
│   └── modules/             # 业务模块
├── frontend/                 # Vue 前端（构建后）
│   └── dist/                # 构建产物
│       └── index.html
└── deploy/                  # 部署配置
    ├── nginx.conf           # Nginx 配置
    ├── supervisor.conf      # Supervisor 配置
    └── .env.server          # 环境变量模板
```
