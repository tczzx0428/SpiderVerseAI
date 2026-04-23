#!/bin/bash
set -e

echo "========================================="
echo "  PulseTeach-AI 完整部署（国内优化版）"
echo "  使用多个稳定国内镜像源"
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
echo "=== Step 1: 配置稳定的国内Docker镜像源 ==="
cat > /etc/docker/daemon.json << 'EOF'
{
  "registry-mirrors": [
    "https://dockerproxy.com",
    "https://docker.m.daocloud.io",
    "https://docker.mirrors.ustc.edu.cn",
    "https://docker.nju.edu.cn",
    "https://hub-mirror.c.163.com"
  ]
}
EOF
systemctl restart docker
sleep 3
log "Docker镜像源配置完成:"
docker info 2>/dev/null | grep -A6 "Registry Mirrors" || true

echo ""
echo "=== Step 2: 创建Docker网络 ==="
docker network create pt_space_tool-platform-network 2>/dev/null || log "网络已存在"

echo ""
echo "=== Step 3: 构建后端镜像 ==="
cd backend
docker build -t tool-platform-backend:latest . 2>&1 | tail -5
if [ $? -eq 0 ]; then
    log "✅ 后端镜像构建成功"
else
    err "❌ 后端镜像构建失败"
fi
cd ..

echo ""
echo "=== Step 4: 构建前端镜像 ==="
cd frontend
docker build -t tool-platform-frontend:latest . 2>&1 | tail -10
if [ $? -eq 0 ]; then
    log "✅ 前端镜像构建成功"
else
    err "❌ 前端镜像构建失败，尝试备用方案..."
    # 备用方案：直接拉取基础镜像再构建
    docker pull node:20-alpine || docker pull dockerproxy.com/library/node:20-alpine
    docker pull nginx:alpine || docker pull dockerproxy.com/library/nginx:alpine
    docker build -t tool-platform-frontend:latest . 2>&1 | tail -5
    if [ $? -eq 0 ]; then
        log "✅ 前端镜像（备用方案）构建成功"
    else
        err "❌ 前端镜像构建仍然失败"
        exit 1
    fi
fi
cd ..

echo ""
echo "=== Step 5: 启动所有服务 ==="
mkdir -p /opt/PT_Space/uploads
chmod -R 777 /opt/PT_Space/uploads
docker compose up -d 2>&1
sleep 20

echo ""
echo "=== Step 6: 检查服务状态 ==="
docker compose ps

echo ""
echo "=== Step 7: 执行数据库迁移 ==="
if docker compose ps | grep -q "backend.*running"; then
    docker compose exec -T backend alembic upgrade head 2>&1 && log "数据库迁移成功" || warn "数据库迁移可能需要稍后手动执行"
else
    warn "后端服务未运行，跳过数据库迁移"
fi

echo ""
echo "========================================="
echo -e "${GREEN}  🎉 部署完成！${NC}"
echo "========================================="
echo ""
echo "访问地址:"
echo "  主页面: http://120.48.141.50"
echo "  API文档: http://120.48.141.50/api/docs"
echo ""
echo "管理命令 (在服务器上执行):"
echo "  cd /opt/PulseTeach\\ AI"
echo "  docker compose ps      # 查看状态"
echo "  docker compose logs -f # 查看日志"
echo "  docker compose down    # 停止服务"
echo "  docker compose restart # 重启服务"
echo ""
echo "团队成员安装:"
echo "  curl -fsSL http://120.48.141.50:8080/install.sh | bash"
echo ""
echo -e "${YELLOW}⚠️  请确保百度云安全组开放端口: 80, 443, 8080${NC}"
echo "========================================="