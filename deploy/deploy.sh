#!/bin/bash
# ============================================
# JNU Link 部署脚本
# 用于将项目部署到阿里云服务器
# ============================================

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置区域 - 请根据实际情况修改
SERVER_USER="root"                    # 服务器用户名
SERVER_HOST="你的服务器IP"               # 服务器IP地址或域名
SERVER_PORT="22"                      # SSH端口
PROJECT_NAME="jnu-link"
DEPLOY_PATH="/var/www/jnu-link"       # 服务器部署路径

# 本地项目路径（相对于脚本所在目录）
LOCAL_PROJECT_PATH="$(cd "$(dirname "$0")/.." && pwd)"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   JNU Link 部署脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# 检查本地环境
echo -e "\n${YELLOW}[1/6] 检查本地环境...${NC}"
if [ ! -d "$LOCAL_PROJECT_PATH/backend" ]; then
    echo -e "${RED}错误：未找到 backend 目录${NC}"
    exit 1
fi
if [ ! -d "$LOCAL_PROJECT_PATH/frontend" ]; then
    echo -e "${RED}错误：未找到 frontend 目录${NC}"
    exit 1
fi
echo -e "${GREEN}✓ 本地项目结构检查通过${NC}"

# 提示配置
if [ "$SERVER_HOST" = "你的服务器IP" ]; then
    echo -e "${YELLOW}请先编辑 deploy.sh 修改 SERVER_HOST 为你的服务器IP${NC}"
    exit 1
fi

# 创建临时目录用于打包
echo -e "\n${YELLOW}[2/6] 准备部署文件...${NC}"
TEMP_DIR="/tmp/jnu-link-deploy-$$"
mkdir -p "$TEMP_DIR"

# 复制项目文件（排除不必要的文件）
echo "复制项目文件..."
rsync -av --exclude='node_modules' \
          --exclude='__pycache__' \
          --exclude='.git' \
          --exclude='*.pyc' \
          --exclude='.env' \
          --exclude='dist' \
          "$LOCAL_PROJECT_PATH/" "$TEMP_DIR/project/"

# 构建前端
echo -e "\n${YELLOW}[3/6] 构建前端...${NC}"
cd "$TEMP_DIR/project/frontend"
npm install
npm run build
echo -e "${GREEN}✓ 前端构建完成${NC}"

# 上传到服务器
echo -e "\n${YELLOW}[4/6] 上传到服务器...${NC}"
ssh -p $SERVER_PORT $SERVER_USER@$SERVER_HOST "mkdir -p $DEPLOY_PATH"
rsync -avz -e "ssh -p $SERVER_PORT" --delete \
    "$TEMP_DIR/project/" "$SERVER_USER@$SERVER_HOST:$DEPLOY_PATH/"

# 安装后端依赖
echo -e "\n${YELLOW}[5/6] 安装服务器依赖...${NC}"
ssh -p $SERVER_PORT $SERVER_USER@$SERVER_HOST << 'ENDSSH'
    cd $DEPLOY_PATH/backend
    pip3 install -r requirements.txt
ENDSSH

# 配置 Nginx 和 Supervisor
echo -e "\n${YELLOW}[6/6] 配置服务...${NC}"
ssh -p $SERVER_PORT $SERVER_USER@$SERVER_HOST << 'ENDSSH'
    # 创建日志目录
    mkdir -p /var/log/jnu-link
    mkdir -p /var/www/jnu-link

    # 复制 Nginx 配置
    cp $DEPLOY_PATH/deploy/nginx.conf /etc/nginx/conf.d/jnu-link.conf

    # 测试 Nginx 配置
    nginx -t

    # 复制 Supervisor 配置
    cp $DEPLOY_PATH/deploy/supervisor.conf /etc/supervisord.d/jnu-link.ini
    supervisorctl reread
    supervisorctl update

    # 重启服务
    systemctl restart nginx
    supervisorctl restart jnu-link-backend

    echo "服务状态："
    supervisorctl status jnu-link-backend
ENDSSH

# 清理
rm -rf "$TEMP_DIR"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}   部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "访问地址: http://$SERVER_HOST"
echo -e "后端API:  http://$SERVER_HOST/api/"
echo -e "\n后续配置："
echo -e "1. 复制 deploy/.env.server 到 backend/.env 并填写实际值"
echo -e "2. 配置阿里云安全组开放 80 端口"
