import json
import logging
from pathlib import Path

from app.config import settings
from app.core.ports.app_repo import IAppRepo

logger = logging.getLogger(__name__)


class ListAllRuns:
    def __init__(self, app_repo: IAppRepo) -> None:
        self._app_repo = app_repo

    def execute(self, current_username: str, current_user_role: str) -> dict:
        apps = self._app_repo.list_all()
        all_runs = []

        for app in apps:
            history_dir = Path(settings.upload_dir) / str(app.id) / "data" / "history"
            if not history_dir.exists():
                continue
            files = sorted(history_dir.glob("*.json"),
                           key=lambda x: x.stat().st_mtime, reverse=True)[:50]
            for f in files:
                try:
                    record = json.loads(f.read_text(encoding="utf-8"))
                    if current_user_role != "admin" and record.get("username") != current_username:
                        continue
                    all_runs.append({
                        **record,
                        "app_id": app.id, "app_name": app.name, "app_slug": app.slug,
                    })
                except Exception as e:
                    logger.warning("解析历史文件 %s 失败: %s", f, e)
                    continue

        all_runs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return {"runs": all_runs[:200]}
