from __future__ import annotations
from app.core.errors import AppBuildInProgress, AppNotFound, Forbidden, NoUploadedCode
from app.core.ports.app_repo import IAppRepo
from app.core.ports.container_runtime import IContainerRuntime
from app.core.ports.route_manager import IRouteManager
from app.core.strategies.app_runtime import IAppRuntime


class DeployApp:
    def __init__(self, app_repo: IAppRepo, container_runtime: IContainerRuntime,
                 route_manager: IRouteManager, runtime: IAppRuntime) -> None:
        self._app_repo = app_repo
        self._container_runtime = container_runtime
        self._route_manager = route_manager
        self._runtime = runtime

    def validate(self, app_id: int, current_user_id: int, current_user_role: str) -> dict:
        """Validate and mark building. Returns app info for background task."""
        app = self._app_repo.get(app_id)
        if not app:
            raise AppNotFound(app_id=app_id)
        if current_user_role != "admin" and app.owner_id != current_user_id:
            raise Forbidden()
        if not app.upload_path:
            raise NoUploadedCode()
        if app.status == "building":
            raise AppBuildInProgress()

        app.status = "building"
        self._app_repo.update(app)

        return {
            "message": "部署任务已提交", "app_id": app_id,
            "status": "building", "access_url": f"/apps/{app.slug}",
        }

    def run_deploy(self, app_id: int) -> None:
        """Execute deployment in background."""
        app = self._app_repo.get(app_id)
        if not app:
            return

        try:
            app.status = "building"
            app.build_log = "开始构建...\n"
            self._app_repo.update(app)

            result = self._container_runtime.build_and_run(
                app_id=app.id, slug=app.slug, build_path=app.upload_path,
                runtime=self._runtime,
            )

            self._route_manager.write_route(
                app_id=app.id, slug=app.slug, host_port=result["host_port"],
            )

            app.status = "running"
            app.container_id = result["container_id"]
            app.container_name = result["container_name"]
            app.host_port = result["host_port"]
            app.build_log = result["build_log"]
            self._app_repo.update(app)

        except Exception as e:
            app.status = "failed"
            app.build_log = (app.build_log or "") + f"\n构建失败: {str(e)}"
            self._app_repo.update(app)
