# PE Space — 内部 AI 工具托管平台

类似 HuggingFace Spaces 的内部工具托管平台，支持一键上传并部署 Streamlit / Gradio 应用，带用户管理、权限控制和使用统计。

访问地址：**http://120.48.9.224**

---

## 功能概览

| 模块 | 说明 |
|------|------|
| 用户认证 | JWT + Cookie 双模式，支持登录/登出，Traefik ForwardAuth 统一鉴权 |
| 应用管理 | 上传 zip → 自动构建 Docker 镜像 → Traefik 动态路由 → 一键启停 |
| 访问控制 | 所有 `/apps/*` 路由强制验证登录；匿名访问自动返回 401 |
| 使用统计 | 记录每个应用的访问次数/访问人数/运行次数/运行人数；统计每位用户活跃度 |
| 用户管理 | 创建/禁用用户；批量创建标注账号；支持账号过期时间 |
| 代码规范 | 管理员可在线编辑「代码规范 Prompt」，用于规范 AI 生成的应用代码 |
| 历史记录 | 每次应用运行自动保存入参/出参 JSON，支持时间轴回看 |

---

## 架构

```
Browser
  │
  ▼
Traefik (80)
  ├── /api/*          → FastAPI 后端 (8000)
  ├── /apps/*         → ForwardAuth 鉴权 → Streamlit 容器 (86xx)
  └── /*              → React 前端 (Nginx)

PostgreSQL           — 用户、应用元数据、访问日志
/opt/PE_Space/uploads — 应用代码、数据、运行历史
traefik/dynamic/     — 动态路由配置（热加载）
```

### ForwardAuth 流程

1. 浏览器携带 `pe_token` Cookie 访问 `/apps/{slug}/...`
2. Traefik 调用 `GET /api/auth/verify-app`，验证 JWT
3. 验证通过 → 注入 `X-PE-User` / `X-PE-Role` / `X-PE-User-Id` Header，记录 `app_views` 访问日志
4. 验证失败 → 直接返回 401

---

## 快速部署

```bash
# 1. 克隆代码
git clone https://github.com/SenWeiV/PE_Space.git && cd PE_Space

# 2. 配置环境变量
cp .env.example .env
# 修改 POSTGRES_PASSWORD、JWT_SECRET、HOST_UPLOAD_DIR、HOST_IP

# 3. 构建镜像
cd backend  && docker build -t tool-platform-backend:latest  . && cd ..
cd frontend && docker build -t tool-platform-frontend:latest . && cd ..

# 4. 创建网络 & 启动
docker network create pe_space_tool-platform-network
docker compose up -d

# 5. 执行数据库迁移
docker compose exec backend alembic upgrade head

# 6. 初始化管理员（使用 API 或直接在 DB 中创建）
```

### 更新部署

```bash
git pull origin main

# 重新构建后端（有代码/依赖变更时）
cd backend  && docker build -t tool-platform-backend:latest  . && cd ..
# 重新构建前端（有前端变更时）
cd frontend && docker build -t tool-platform-frontend:latest . && cd ..

docker compose up -d
docker compose exec backend alembic upgrade head
```

---

## 上传应用要求

zip 包必须包含：

- `app.py` — Streamlit 入口文件
- `requirements.txt` — Python 依赖

平台自动注入 Dockerfile，无需手动提供。

应用代码规范参考「代码规范 Prompt」（管理后台可查看/编辑）。

---

## 目录结构

```
PE_Space/
├── backend/
│   ├── alembic/versions/       # 数据库迁移脚本
│   ├── app/
│   │   ├── core/               # 纯业务逻辑，零外部依赖
│   │   │   ├── entities/       # 业务实体定义
│   │   │   ├── ports/          # 数据库/外部服务抽象接口
│   │   │   ├── usecases/       # 业务逻辑（auth, app, admin, stats, history...）
│   │   │   └── strategies/     # 策略模式实现（认证、运行时）
│   │   ├── infra/              # 基础设施层，实现 port 接口
│   │   │   ├── db/             # SQLAlchemy 模型 + repo 实现
│   │   │   ├── services/       # Docker 运行时、Nginx 路由管理
│   │   │   ├── storage/        # 文件系统存储
│   │   │   └── auth/           # JWT 实现
│   │   ├── api/                # HTTP 接入层（薄适配器）
│   │   │   ├── routes/         # 路由（auth, apps, admin, stats, config, prompts）
│   │   │   ├── schemas/        # Pydantic 请求/响应模型
│   │   │   └── middleware/     # CORS、统一错误处理
│   │   ├── container.py        # 依赖注入，组装所有依赖
│   │   └── main.py
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── admin/          # UserManagePage, TemplateManagePage, StatsPage
│   │   │   └── ...             # HomePage, AppsListPage, AppDetailPage, HistoryPage
│   │   ├── api/                # axios client + typed API wrappers
│   │   └── store/              # authStore (Zustand)
│   └── Dockerfile
├── traefik/
│   ├── traefik.yml             # 静态配置
│   └── dynamic/
│       ├── base.yml            # 后端/前端路由 + pe-auth ForwardAuth 中间件
│       └── app_*.yml           # 每个运行中应用的动态路由（自动生成）
├── docker-compose.yml
└── .env.example
```

---

## 角色权限

| 角色 | 权限 |
|------|------|
| `admin` | 全部功能，含用户管理、统计、模板编辑 |
| `user` | 首页、应用管理（上传/启停）、历史记录 |
| `annotator` | 仅首页 + 应用管理（使用工具），无历史记录 |

---

## 路线图

- [ ] **CLI 工具**：`pe deploy` 直接从本地上传并部署，无需手动压缩上传
- [ ] **前后端分离部署**：支持 FastAPI + React 等多容器应用
- [ ] **需求驱动部署**：页面描述需求 → AI 自动生成代码 → 自动部署
- [ ] **应用版本管理**：回滚到历史版本
