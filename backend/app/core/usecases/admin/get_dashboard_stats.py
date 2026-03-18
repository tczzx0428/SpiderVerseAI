from app.core.ports.app_repo import IAppRepo
from app.core.ports.user_repo import IUserRepo
from app.infra.db.repos.app_repo import SqlAlchemyAppRepo


class GetDashboardStats:
    def __init__(self, app_repo: IAppRepo, user_repo: IUserRepo) -> None:
        self._app_repo = app_repo
        self._user_repo = user_repo

    def execute(self) -> dict:
        # Use count methods if available
        repo = self._app_repo
        if isinstance(repo, SqlAlchemyAppRepo):
            return {
                "total_users": self._user_repo.count(),
                "total_apps": repo.count(),
                "running_apps": repo.count(status="running"),
                "failed_apps": repo.count(status="failed"),
            }
        # Fallback
        apps = self._app_repo.list_all()
        return {
            "total_users": self._user_repo.count(),
            "total_apps": len(apps),
            "running_apps": sum(1 for a in apps if a.status == "running"),
            "failed_apps": sum(1 for a in apps if a.status == "failed"),
        }
