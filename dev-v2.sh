#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🚀 启动重构版本开发环境 (v2)..."
echo "   ⚠️  使用独立端口，不影响现有项目"
echo "   Backend:  8001"
echo "   Frontend: 5174"
echo "   Postgres: 5434"
echo ""

# 创建本地目录
mkdir -p /tmp/pe_uploads_v2 /tmp/traefik-dynamic-v2

# 启动所有服务
cd "$PROJECT_DIR"
docker compose -f docker-compose.dev-v2.yml up -d --build postgres backend

echo "⏳ 等待后端就绪..."
for i in $(seq 1 60); do
  if curl -s http://localhost:8001/api/health > /dev/null 2>&1; then
    echo "✅ 后端已就绪"
    break
  fi
  if [ $i -eq 60 ]; then
    echo "❌ 后端启动超时，查看日志："
    docker logs backend_dev_v2 --tail 30
    exit 1
  fi
  sleep 1
done

# 执行数据库迁移
echo "🗄️  执行数据库迁移..."
docker compose -f docker-compose.dev-v2.yml exec backend alembic upgrade head

# 检查是否有 admin 用户
echo "👤 检查管理员账号..."
docker compose -f docker-compose.dev-v2.yml exec backend python3 -c "
from app.infra.db.database import SessionLocal
from app.infra.db.models.user import User
from app.infra.auth.jwt_auth import JwtAuthProvider
auth = JwtAuthProvider()
db = SessionLocal()
if not db.query(User).filter(User.username == 'admin').first():
    db.add(User(username='admin', hashed_pw=auth.hash_password('admin123'), role='admin', is_active=True))
    db.commit()
    print('✅ 已创建 admin / admin123')
else:
    print('✅ admin 账号已存在')
db.close()
" 2>&1 | grep -v "trapped\|bcrypt version"

# 启动前端
cd "$PROJECT_DIR/frontend"
if [ ! -d "node_modules" ]; then
  echo "📦 安装前端依赖..."
  npm install
fi

echo ""
echo "✅ 重构版本开发环境启动完毕！"
echo "   前端：http://localhost:5174"
echo "   后端：http://localhost:8001/api/docs"
echo "   账号：admin / admin123"
echo ""
echo "   📌 现有项目仍在 :8000 / :5173 运行"
echo ""

VITE_API_TARGET=http://localhost:8001 npx vite --host --port 5174
