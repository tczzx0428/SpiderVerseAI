from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from pathlib import Path

# Register ORM models so Alembic/SQLAlchemy can see all tables
from app.infra.db.models import app as _app_model  # noqa: F401
from app.infra.db.models import app_view as _app_view_model  # noqa: F401
from app.infra.db.models import config as _config_model  # noqa: F401
from app.infra.db.models import prompt as _prompt_model  # noqa: F401
from app.infra.db.models import user as _user_model  # noqa: F401
from app.infra.db.models import ai_creation as _ai_creation_model  # noqa: F401

from app.api.middleware.cors import setup_cors
from app.api.middleware.error_handler import setup_error_handlers
from app.api.routes import admin, apps, auth, config as config_routes, prompts, skills, skills_cli, stats, ai_create

app = FastAPI(title="Tool Platform API", version="2.0.0")

setup_cors(app)
setup_error_handlers(app)

app.include_router(auth.router)
app.include_router(apps.router)
app.include_router(prompts.router)
app.include_router(admin.router)
app.include_router(config_routes.router)
app.include_router(skills.router)
app.include_router(skills_cli.router)
app.include_router(stats.router)
app.include_router(ai_create.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/install.sh", response_class=PlainTextResponse)
def install_script():
    """提供一键安装脚本下载（无需登录）"""
    script_path = Path("/install.sh")
    if script_path.exists():
        return PlainTextResponse(
            content=script_path.read_text(),
            media_type="text/x-sh",
            headers={"Content-Disposition": "inline; filename=install.sh"},
        )
    return PlainTextResponse("# Script not found\n", status_code=404)
