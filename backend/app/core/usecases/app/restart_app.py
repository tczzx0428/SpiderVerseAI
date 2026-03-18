from app.core.errors import AppNotFound, Forbidden, NoContainer
from app.core.ports.app_repo import IAppRepo
from app.core.ports.container_runtime import IContainerRuntime
from app.core.ports.route_manager import IRouteManager


class RestartApp:
    def __init__(self, app_repo: IAppRepo, container_runtime: IContainerRuntime,
                 route_manager: IRouteManager) -> None:
        self._app_repo = app_repo
        self._container_runtime = container_runtime
        self._route_manager = route_manager

    def execute(self, app_id: int, current_user_id: int, current_user_role: str) -> dict:
        app = self._app_repo.get(app_id)
        if not app:
            raise AppNotFound(app_id=app_id)
        if current_user_role != "admin" and app.owner_id != current_user_id:
            raise Forbidden()
        if not app.container_name:
            raise NoContainer()

        self._container_runtime.restart(app.container_name)

        if app.host_port:
            self._route_manager.write_route(app_id, app.slug, app.host_port)

        app.status = "running"
        self._app_repo.update(app)
        return {"message": "已重启", "app_id": app_id}
