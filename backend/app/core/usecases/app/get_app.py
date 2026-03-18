from app.core.errors import AppNotFound
from app.core.ports.app_repo import IAppRepo
from app.core.ports.user_repo import IUserRepo


class GetApp:
    def __init__(self, app_repo: IAppRepo, user_repo: IUserRepo) -> None:
        self._app_repo = app_repo
        self._user_repo = user_repo

    def execute(self, app_id: int) -> dict:
        app = self._app_repo.get(app_id)
        if not app:
            raise AppNotFound(app_id=app_id)
        owner = self._user_repo.get(app.owner_id)
        return {
            "id": app.id, "name": app.name, "slug": app.slug,
            "description": app.description, "status": app.status,
            "host_port": app.host_port, "build_log": app.build_log,
            "access_url": f"/apps/{app.slug}" if app.status == "running" else None,
            "owner": owner, "created_at": app.created_at, "updated_at": app.updated_at,
        }


class GetAppBySlug:
    def __init__(self, app_repo: IAppRepo, user_repo: IUserRepo) -> None:
        self._app_repo = app_repo
        self._user_repo = user_repo

    def execute(self, slug: str) -> dict:
        app = self._app_repo.get_by_slug(slug)
        if not app:
            raise AppNotFound(slug=slug)
        owner = self._user_repo.get(app.owner_id)
        return {
            "id": app.id, "name": app.name, "slug": app.slug,
            "description": app.description, "status": app.status,
            "host_port": app.host_port, "build_log": app.build_log,
            "access_url": f"/apps/{app.slug}" if app.status == "running" else None,
            "owner": owner, "created_at": app.created_at, "updated_at": app.updated_at,
        }
