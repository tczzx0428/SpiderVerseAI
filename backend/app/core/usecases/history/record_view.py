import json
import uuid
from pathlib import Path

from app.config import settings
from app.core.ports.app_repo import IAppRepo
from app.core.shared.time_utils import now_cst


class RecordView:
    def __init__(self, app_repo: IAppRepo) -> None:
        self._app_repo = app_repo

    def execute(self, app_id: int, username: str = "anonymous") -> dict:
        app = self._app_repo.get(app_id)
        if not app:
            return {"ok": False, "reason": "app not found"}

        username = username or "anonymous"
        tracking_dir = Path(settings.upload_dir) / str(app_id) / "data" / "history" / "_tracking"
        tracking_dir.mkdir(parents=True, exist_ok=True)

        view_id = str(uuid.uuid4())
        record = {
            "run_id": view_id, "type": "view", "username": username,
            "timestamp": now_cst().isoformat(),
            "app_id": app_id, "app_name": app.name,
        }
        (tracking_dir / f"{view_id}.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"ok": True}
