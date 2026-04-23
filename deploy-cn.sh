#!/bin/bash
set -e

echo "========================================="
echo "  PulseTeach-AI 部署脚本（国内镜像版）"
echo "========================================="

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[✓] $1${NC}"; }
warn() { echo -e "${YELLOW}[!] $1${NC}"; }
err() { echo -e "${RED}[✗] $1${NC}"; exit 1; }

echo ""
log "Step 1/7: 安装Docker（使用阿里云镜像源）..."
if ! command -v docker &> /dev/null; then
    apt-get update -qq
    apt-get install -y -qq apt-transport-https ca-certificates curl software-properties-common gnupg lsb-release
    
    # 使用阿里云Docker镜像源
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc
    
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://mirrors.aliyun.com/docker-ce/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" > /etc/apt/sources.list.d/docker.list
    
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin docker-buildx-plugin
    
    systemctl start docker
    systemctl enable docker
    
    # 配置Docker镜像加速器
    mkdir -p /etc/docker
    cat > /etc/docker/daemon.json << 'DOCKEREOF'
{
  "registry-mirrors": ["https://mirror.ccs.tencentyun.com", "https://docker.mirrors.ustc.edu.cn"]
}
DOCKEREOF
    systemctl restart docker
    
    log "Docker安装完成: $(docker --version)"
else
    log "Docker已安装: $(docker --version)"
fi

echo ""
log "Step 2/7: 克隆PulseTeach-AI项目..."
cd /opt
if [ -d "PulseTeach AI" ]; then
    cd "PulseTeach AI"
    git pull origin main || warn "git pull失败，继续使用现有代码"
else
    git clone https://github.com/tczzx0428/PulseTeach-AI.git "PulseTeach AI"
    cd "PulseTeach AI"
fi
log "项目目录: $(pwd)"

echo ""
log "Step 3/7: 配置环境变量..."
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
    else
        cat > .env << 'ENVEOF'
POSTGRES_PASSWORD=PtSpace2024Secure!
POSTGRES_USER=postgres
POSTGRES_DB=pt_space
JWT_SECRET=AutoGenSecret$(date +%s | sha256sum | head -c 32)
HOST_UPLOAD_DIR=/opt/PT_Space/uploads
HOST_IP=120.48.141.50
TEAM_API_KEY=
TEAM_BASE_URL=
CODEX_MODEL=gpt-4
OPENCLAW_MODEL=gpt-4
ENVEOF
    fi
    sed -i 's/HOST_IP=.*/HOST_IP=120.48.141.50/' .env
    log ".env配置已生成"
else
    warn ".env已存在"
fi

echo ""
log "Step 4/7: 初始化基础设施..."
docker network create pt_space_tool-platform-network 2>/dev/null || true
mkdir -p /opt/PT_Space/uploads
chmod -R 777 /opt/PT_Space/uploads
log "网络和目录就绪"

echo ""
log "Step 5/7: 构建Docker镜像..."
cd backend && docker build -t tool-platform-backend:latest . && log "后端镜像构建完成" || err "后端镜像构建失败"
cd ..
cd frontend && docker build -t tool-platform-frontend:latest . && log "前端镜像构建完成" || err "前端镜像构建失败"
cd ..

echo ""
log "Step 6/7: 启动服务..."
docker compose up -d
sleep 15
log "服务已启动"

echo ""
log "Step 7/7: 数据库迁移..."
docker compose exec -T backend alembic upgrade head 2>&1 || warn "数据库迁移可能需要稍后手动执行"
log "数据库初始化完成"

echo ""
echo "========================================="
echo -e "${GREEN}  🎉 部署成功完成！${NC}"
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
echo ""
echo "团队成员安装:"
echo "  curl -fsSL http://120.48.141.50:8080/install.sh | bash"
echo ""
echo -e "${YELLOW}⚠️  请确保百度云安全组开放端口: 80, 443, 8080${NC}"
echo "========================================="