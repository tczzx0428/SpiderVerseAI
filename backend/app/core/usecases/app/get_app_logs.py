from app.core.errors import AppNotFound
from app.core.ports.app_repo import IAppRepo


class GetAppLogs:
    def __init__(self, app_repo: IAppRepo) -> None:
        self._app_repo = app_repo

    def execute(self, app_id: int) -> dict:
        app = self._app_repo.get(app_id)
        if not app:
            raise AppNotFound(app_id=app_id)
        return {"app_id": app_id, "status": app.status, "log": app.build_log or ""}
