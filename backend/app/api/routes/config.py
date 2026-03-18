from __future__ import annotations
from fastapi import APIRouter, Depends

from app.api.deps import get_container, get_current_user, require_admin
from app.api.schemas.config import ConfigHistoryOut, ConfigOut, ConfigUpdate
from app.container import Container
from app.infra.db.models.user import User

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("/template", response_model=ConfigOut)
def get_template(c: Container = Depends(get_container),
                 current_user: User = Depends(get_current_user)):
    return c.get_template.execute()


@router.put("/template", response_model=ConfigOut)
def update_template(body: ConfigUpdate, c: Container = Depends(get_container),
                    admin: User = Depends(require_admin)):
    return c.update_template.execute(body.value, admin.id, admin.username)


@router.get("/template/history", response_model=list[ConfigHistoryOut])
def get_template_history(c: Container = Depends(get_container),
                         admin: User = Depends(require_admin)):
    return c.get_template_history.execute()
