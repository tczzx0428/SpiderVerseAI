from __future__ import annotations
from typing import Optional

from app.core.errors import AppNotFound, UserNotFound
from app.core.ports.app_repo import IAppRepo
from app.core.ports.user_repo import IUserRepo


class UpdateApp:
    def __init__(self, app_repo: IAppRepo, user_repo: IUserRepo) -> None:
        self._app_repo = app_repo
        self._user_repo = user_repo

    def execute(self, app_id: int, name: Optional[str] = None,
                description: Optional[str] = None, owner_id: Optional[int] = None) -> dict:
        app = self._app_repo.get(app_id)
        if not app:
            raise AppNotFound(app_id=app_id)

        if name is not None:
            app.name = name
        if description is not None:
            app.description = description
        if owner_id is not None:
            if not self._user_repo.get(owner_id):
                raise UserNotFound(user_id=owner_id)
            app.owner_id = owner_id

        updated = self._app_repo.update(app)
        owner = self._user_repo.get(updated.owner_id)
        return {
            "id": updated.id, "name": updated.name, "slug": updated.slug,
            "description": updated.description, "status": updated.status,
            "host_port": updated.host_port, "build_log": updated.build_log,
            "access_url": f"/apps/{updated.slug}" if updated.status == "running" else None,
            "owner": owner, "created_at": updated.created_at, "updated_at": updated.updated_at,
        }
