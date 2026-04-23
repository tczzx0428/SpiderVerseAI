#!/bin/bash
echo "=== 修复Docker镜像源 ==="
cat > /etc/docker/daemon.json << 'EOF'
{
  "registry-mirrors": [
    "https://docker.1ms.run",
    "https://docker.xuanyuan.me",
    "https://dockerproxy.com"
  ]
}
EOF
systemctl restart docker
sleep 3
echo "Docker镜像源已更新:"
docker info 2>/dev/null | grep -A5 "Registry Mirrors" || echo "检查镜像源配置..."
echo ""
echo "=== 继续构建镜像 ==="
cd /opt/PulseTeach\ AI
echo "构建后端镜像..."
cd backend && docker build -t tool-platform-backend:latest . 2>&1 | tail -10
BACKEND_STATUS=$?
cd ..
if [ $BACKEND_STATUS -eq 0 ]; then
    echo "✅ 后端镜像构建成功"
else
    echo "❌ 后端镜像构建失败"
    exit 1
fi

echo "构建前端镜像..."
cd frontend && docker build -t tool-platform-frontend:latest . 2>&1 | tail -10
FRONTEND_STATUS=$?
cd ..
if [ $FRONTEND_STATUS -eq 0 ]; then
    echo "✅ 前端镜像构建成功"
else
    echo "❌ 前端镜像构建失败"
    exit 1
fi

echo ""
echo "=== 启动服务 ==="
docker compose up -d
sleep 15

echo ""
echo "=== 数据库迁移 ==="
docker compose exec -T backend alembic upgrade head 2>&1 || echo "数据库迁移可能需要稍后手动执行"

echo ""
echo "========================================="
echo "  🎉 部署完成！"
echo "========================================="
echo "访问地址: http://120.48.141.50"
echo "API文档: http://120.48.141.50/api/docs"
echo "========================================="