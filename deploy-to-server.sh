#!/bin/bash
set -e

echo "========================================="
echo "  PulseTeach-AI 自动部署脚本"
echo "========================================="

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}错误: 请使用root用户运行此脚本${NC}"
    exit 1
fi

echo -e "${GREEN}[1/8] 检查系统环境...${NC}"

if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "操作系统: $NAME $VERSION"
fi

echo -e "${GREEN}[2/8] 检查并安装Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo "安装Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl start docker
    systemctl enable docker
    echo -e "${GREEN}Docker安装完成${NC}"
else
    echo -e "${GREEN}Docker已安装: $(docker --version)${NC}"
fi

echo -e "${GREEN}[3/8] 克隆项目代码...${NC}"
cd /opt
if [ -d "PulseTeach-AI" ]; then
    cd PulseTeach-AI
    git pull origin main
else
    git clone https://github.com/tczzx0428/PulseTeach-AI.git "PulseTeach AI"
    cd "PulseTeach AI"
fi

echo -e "${GREEN}[4/8] 配置环境变量...${NC}"
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
    else
        cat > .env << 'ENVEOF'
POSTGRES_PASSWORD=PtSpace2024Secure!
POSTGRES_USER=postgres
POSTGRES_DB=pt_space
JWT_SECRET=$(openssl rand -hex 32)
HOST_UPLOAD_DIR=/opt/PT_Space/uploads
HOST_IP=120.48.141.50
TEAM_API_KEY=
TEAM_BASE_URL=
CODEX_MODEL=gpt-4
OPENCLAW_MODEL=gpt-4
ENVEOF
    fi
    echo -e "${GREEN}已生成.env配置文件${NC}"
    echo -e "${YELLOW}请根据需要编辑 /opt/PulseTeach\\ AI/.env${NC}"
fi

echo -e "${GREEN}[5/8] 创建网络和目录...${NC}"
docker network create pt_space_tool-platform-network 2>/dev/null || true
mkdir -p /opt/PT_Space/uploads
chmod -R 777 /opt/PT_Space/uploads

echo -e "${GREEN}[6/8] 构建Docker镜像...${NC}"
cd backend && docker build -t tool-platform-backend:latest . && cd ..
cd frontend && docker build -t tool-platform-frontend:latest . && cd ..

echo -e "${GREEN}[7/8] 启动服务...${NC}"
docker compose up -d

sleep 10

echo -e "${GREEN}[8/8] 执行数据库迁移...${NC}"
docker compose exec backend alembic upgrade head

echo ""
echo "========================================="
echo -e "${GREEN}  🎉 部署完成！${NC}"
echo "========================================="
echo ""
echo "访问地址: http://120.48.141.50"
echo "API文档:  http://120.48.141.50/api/docs"
echo ""
echo "常用管理命令:"
echo "  docker compose ps        # 查看状态"
echo "  docker compose logs -f   # 查看日志"
echo "  docker compose down      # 停止服务"
echo "  docker compose restart   # 重启服务"
echo ""
echo "团队成员安装:"
echo "  curl -fsSL http://120.48.141.50:8080/install.sh | bash"
echo ""
echo -e "${YELLOW}请确保防火墙开放端口: 80, 443, 8080${NC}"
echo "========================================="