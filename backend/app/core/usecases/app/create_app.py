from __future__ import annotations
from app.core.entities.app import AppEntity
from app.core.errors import SlugTaken
from app.core.ports.app_repo import IAppRepo
from app.core.ports.user_repo import IUserRepo


class CreateApp:
    def __init__(self, app_repo: IAppRepo, user_repo: IUserRepo) -> None:
        self._app_repo = app_repo
        self._user_repo = user_repo

    def execute(self, name: str, slug: str, description: str | None, owner_id: int) -> dict:
        if self._app_repo.get_by_slug(slug):
            raise SlugTaken(slug)

        entity = AppEntity(id=0, name=name, slug=slug, description=description,
                           owner_id=owner_id, status="pending")
        created = self._app_repo.create(entity)
        owner = self._user_repo.get(owner_id)

        return {
            "id": created.id, "name": created.name, "slug": created.slug,
            "description": created.description, "status": created.status,
            "host_port": created.host_port, "build_log": created.build_log,
            "access_url": None, "owner": owner,
            "created_at": created.created_at, "updated_at": created.updated_at,
        }
