import json
from pathlib import Path

from app.config import settings
from app.core.errors import AppNotFound
from app.core.ports.app_repo import IAppRepo


class GetAppHistory:
    def __init__(self, app_repo: IAppRepo) -> None:
        self._app_repo = app_repo

    def execute(self, app_id: int, current_username: str, current_user_role: str) -> list:
        app = self._app_repo.get(app_id)
        if not app:
            raise AppNotFound(app_id=app_id)

        history_dir = Path(settings.upload_dir) / str(app_id) / "data" / "history"
        if not history_dir.exists():
            return []

        records = []
        for f in history_dir.glob("*.json"):
            try:
                record = json.loads(f.read_text(encoding="utf-8"))
                if current_user_role != "admin" and record.get("username") != current_username:
                    continue
                records.append(record)
            except Exception:
                continue

        return sorted(records, key=lambda x: x.get("timestamp", ""), reverse=True)
