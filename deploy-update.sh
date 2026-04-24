#!/bin/bash
set -e

echo "========================================="
echo "  PulseTeach-AI 快速更新部署"
echo "========================================="

cd /opt/PulseTeach\ AI

echo "📥 [1/4] 拉取最新代码..."
git pull origin main

echo "🛑 [2/4] 停止旧服务..."
docker compose down

echo "🔨 [3/4] 重新构建并启动..."
docker compose up -d --build

echo "⏳ 等待服务启动..."
sleep 15

echo "🗄️  [4/4] 执行数据库迁移..."
docker compose exec backend alembic upgrade head

echo ""
echo "========================================="
echo -e "  ✅ 部署完成！"
echo "========================================="
echo ""
docker compose ps
echo ""
echo "🌐 访问地址: http://120.48.141.50"
echo "📚 API文档: http://120.48.141.50/api/docs"
