#!/bin/bash
set -e

echo "========================================="
echo "  PulseTeach-AI 更新部署"
echo "  「创作应用」功能上线"
echo "========================================="

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[✓] $1${NC}"; }
warn() { echo -e "${YELLOW}[!] $1${NC}"; }
err() { echo -e "${RED}[✗] $1${NC}"; }

cd /opt/PulseTeach\ AI

echo ""
echo "=== Step 1: 拉取最新代码 ==="
git pull origin main
log "代码更新完成"

echo ""
echo "=== Step 2: 执行数据库迁移 ==="
docker compose exec -T backend alembic upgrade head
log "数据库迁移完成"

echo ""
echo "=== Step 3: 重新构建镜像 ==="
echo "构建后端..."
cd backend && docker build -t tool-platform-backend:latest . 2>&1 | tail -5
BACKEND_STATUS=$?
cd ..
if [ $BACKEND_STATUS -ne 0 ]; then
    err "后端构建失败"
    exit 1
fi
log "后端镜像构建完成"

echo "构建前端..."
cd frontend && docker build -t tool-platform-frontend:latest . 2>&1 | tail -5
FRONTEND_STATUS=$?
cd ..
if [ $FRONTEND_STATUS -ne 0 ]; then
    err "前端构建失败"
    exit 1
fi
log "前端镜像构建完成"

echo ""
echo "=== Step 4: 重启服务 ==="
docker compose up -d
sleep 5

echo ""
echo "=== Step 5: 验证服务状态 ==="
docker compose ps

echo ""
echo "========================================="
echo "  🎉 部署完成！"
echo "========================================="
echo ""
echo "访问地址:"
echo "  主页面: http://120.48.141.50"
echo "  创作应用: http://120.48.141.50/create"
echo "  API文档: http://120.48.141.50/api/docs"
echo ""