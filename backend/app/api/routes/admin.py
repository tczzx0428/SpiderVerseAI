from __future__ import annotations
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from app.api.deps import get_container, require_admin
from app.api.schemas.user import BatchUserCreate, UserCreate, UserOut, UserUpdate
from app.container import Container
from app.infra.db.models.user import User

router = APIRouter(prefix="/api/admin", tags=["admin"])


class SkillUpdate(BaseModel):
    content: str


class TeamConfigUpdate(BaseModel):
    api_key: str | None = None
    base_url: str | None = None
    codex_model: str | None = None
    openclaw_model: str | None = None
    ai_api_key: str | None = None
    ai_base_url: str | None = None
    ai_model: str | None = None
    ai_code_model: str | None = None


@router.get("/skills")
def list_skills_admin(c: Container = Depends(get_container),
                      admin: User = Depends(require_admin)):
    return c.list_skills_admin.execute()


@router.put("/skills/{name}", status_code=200)
def upsert_skill(name: str, body: SkillUpdate,
                 c: Container = Depends(get_container),
                 admin: User = Depends(require_admin)):
    return c.upsert_skill.execute(name, body.content, admin.id, admin.username)


@router.delete("/skills/{name}", status_code=204)
def delete_skill(name: str, c: Container = Depends(get_container),
                 admin: User = Depends(require_admin)):
    c.delete_skill.execute(name)


@router.put("/team-config")
def update_team_config(body: TeamConfigUpdate,
                       c: Container = Depends(get_container),
                       admin: User = Depends(require_admin)):
    updates = body.model_dump(exclude_none=True)
    if not updates:
        return {"ok": True, "updated": []}
    return c.update_team_config.execute(updates, admin.id, admin.username)


@router.get("/users", response_model=list[UserOut])
def list_users(c: Container = Depends(get_container),
               admin: User = Depends(require_admin)):
    users = c.update_user._user_repo.list_all()
    return [UserOut.model_validate(u) for u in users]


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(body: UserCreate, c: Container = Depends(get_container),
                admin: User = Depends(require_admin)):
    user = c.create_user.execute(body.username, body.password, body.email,
                                 body.role, body.expires_at)
    return UserOut.model_validate(user)


@router.post("/users/batch", response_model=list[UserOut], status_code=status.HTTP_201_CREATED)
def batch_create_users(body: BatchUserCreate, c: Container = Depends(get_container),
                       admin: User = Depends(require_admin)):
    users = c.batch_create_users.execute(body.project_name, body.start_index,
                                         body.count, body.password, body.expires_at)
    return [UserOut.model_validate(u) for u in users]


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, body: UserUpdate, c: Container = Depends(get_container),
                admin: User = Depends(require_admin)):
    user = c.update_user.execute(user_id, **body.model_dump(exclude_none=True))
    return UserOut.model_validate(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, c: Container = Depends(get_container),
                admin: User = Depends(require_admin)):
    c.delete_user.execute(user_id, admin.id)


@router.get("/stats")
def get_stats(c: Container = Depends(get_container),
              admin: User = Depends(require_admin)):
    return c.get_dashboard_stats.execute()
