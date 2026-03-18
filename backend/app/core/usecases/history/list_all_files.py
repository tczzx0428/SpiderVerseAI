from datetime import datetime
from pathlib import Path

from app.config import settings
from app.core.ports.app_repo import IAppRepo
from app.core.shared.time_utils import CST


class ListAllFiles:
    def __init__(self, app_repo: IAppRepo) -> None:
        self._app_repo = app_repo

    def execute(self, current_user_id: int, current_user_role: str) -> dict:
        apps = self._app_repo.list_all()
        all_files = []

        for app in apps:
            if current_user_role != "admin" and app.owner_id != current_user_id:
                continue
            data_dir = Path(settings.upload_dir) / str(app.id) / "data"
            if not data_dir.exists():
                continue
            for f in data_dir.rglob("*"):
                if f.is_file() and not f.name.startswith("."):
                    stat = f.stat()
                    all_files.append({
                        "app_id": app.id, "app_name": app.name, "app_slug": app.slug,
                        "name": f.name,
                        "path": str(f.relative_to(data_dir)),
                        "size": stat.st_size,
                        "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=CST).isoformat(),
                    })

        all_files.sort(key=lambda x: x["modified_at"], reverse=True)
        return {"files": all_files[:500]}
