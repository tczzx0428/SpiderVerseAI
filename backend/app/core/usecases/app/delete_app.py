from pathlib import Path

from app.core.errors import AppNotFound, Forbidden
from app.core.ports.app_repo import IAppRepo
from app.core.ports.container_runtime import IContainerRuntime
from app.core.ports.route_manager import IRouteManager
from app.infra.storage.filesystem import LocalFileStorage


class DeleteApp:
    def __init__(self, app_repo: IAppRepo, container_runtime: IContainerRuntime,
                 route_manager: IRouteManager, storage: LocalFileStorage) -> None:
        self._app_repo = app_repo
        self._container_runtime = container_runtime
        self._route_manager = route_manager
        self._storage = storage

    def execute(self, app_id: int, current_user_id: int, current_user_role: str) -> None:
        app = self._app_repo.get(app_id)
        if not app:
            raise AppNotFound(app_id=app_id)
        if current_user_role != "admin" and app.owner_id != current_user_id:
            raise Forbidden()

        if app.container_name:
            self._container_runtime.remove(app.container_name)
        self._route_manager.remove_route(app_id)

        if app.upload_path:
            self._storage.remove_tree(Path(app.upload_path))

        self._app_repo.delete(app_id)
