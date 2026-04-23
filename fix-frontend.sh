#!/bin/bash
echo "=== 修复前端镜像构建 ==="

cd /opt/PulseTeach\ AI

echo "1. 清理Docker缓存..."
docker system prune -f 2>/dev/null

echo ""
echo "2. 尝试使用官方Docker源（移除镜像加速器）..."
cat > /etc/docker/daemon.json << 'EOF'
{}
EOF
systemctl restart docker
sleep 3

echo ""
echo "3. 重新构建前端镜像（使用官方源，可能较慢）..."
cd frontend
docker build --no-cache -t tool-platform-frontend:latest . 2>&1 | tee /tmp/frontend_build.log
FRONTEND_STATUS=$?
cd ..

if [ $FRONTEND_STATUS -eq 0 ]; then
    echo ""
    echo "✅ 前端镜像构建成功！"
    echo ""
    echo "4. 启动所有服务..."
    docker compose up -d
    sleep 20
    
    echo ""
    echo "5. 检查服务状态..."
    docker compose ps
    
    echo ""
    echo "6. 执行数据库迁移..."
    docker compose exec -T backend alembic upgrade head 2>&1 || echo "数据库迁移可能需要稍后手动执行"
    
    echo ""
    echo "========================================="
    echo "  🎉 部署完成！"
    echo "========================================="
    echo "访问地址: http://120.48.141.50"
    echo "API文档: http://120.48.141.50/api/docs"
    echo "========================================="
else
    echo ""
    echo "❌ 前端镜像构建仍然失败"
    echo "尝试备用方案：使用阿里云容器镜像服务..."
    
    cat > /etc/docker/daemon.json << 'EOF'
{
  "registry-mirrors": ["https://registry.cn-hangzhou.aliyuncs.com"]
}
EOF
    systemctl restart docker
    sleep 3
    
    cd frontend
    docker build --no-cache -t tool-platform-frontend:latest . 2>&1 | tail -20
    cd ..
fi