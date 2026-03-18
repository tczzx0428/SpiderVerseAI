from __future__ import annotations
from typing import Optional

from app.core.ports.app_repo import IAppRepo
from app.core.ports.user_repo import IUserRepo


class ListApps:
    def __init__(self, app_repo: IAppRepo, user_repo: IUserRepo) -> None:
        self._app_repo = app_repo
        self._user_repo = user_repo

    def execute(self, page: int = 1, size: int = 20, status: Optional[str] = None) -> dict:
        apps, total = self._app_repo.list(page=page, size=size, status=status)
        owner_ids = list({a.owner_id for a in apps})
        owners = self._user_repo.get_batch(owner_ids)

        items = []
        for app in apps:
            owner = owners.get(app.owner_id)
            items.append({
                "id": app.id, "name": app.name, "slug": app.slug,
                "description": app.description, "status": app.status,
                "access_url": f"/apps/{app.slug}" if app.status == "running" else None,
                "owner": owner, "created_at": app.created_at, "updated_at": app.updated_at,
            })

        return {"total": total, "page": page, "size": size, "items": items}
