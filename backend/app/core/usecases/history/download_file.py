from __future__ import annotations
from pathlib import Path

from app.config import settings
from app.core.errors import AppNotFound, Forbidden


class DownloadFile:
    def __init__(self, app_repo) -> None:
        self._app_repo = app_repo

    def get_output_path(self, app_id: int, run_id: str, filename: str,
                        current_user_id: int, current_user_role: str) -> Path:
        app = self._app_repo.get(app_id)
        if not app:
            raise AppNotFound(app_id=app_id)
        if current_user_role != "admin" and app.owner_id != current_user_id:
            raise Forbidden("无权限访问")

        allowed_base = (Path(settings.upload_dir) / str(app_id) / "data" / "outputs").resolve()
        file_path = (allowed_base / run_id / filename).resolve()

        if not str(file_path).startswith(str(allowed_base)):
            raise Forbidden("访问被拒绝")
        if not file_path.exists():
            raise FileNotFoundError("文件不存在")
        return file_path

    def get_data_file_path(self, app_id: int, file_path_str: str,
                           current_user_id: int, current_user_role: str) -> Path:
        app = self._app_repo.get(app_id)
        if not app:
            raise AppNotFound(app_id=app_id)
        if current_user_role != "admin" and app.owner_id != current_user_id:
            raise Forbidden("无权限访问")

        allowed_base = (Path(settings.upload_dir) / str(app_id) / "data").resolve()
        target = (allowed_base / file_path_str).resolve()

        if not str(target).startswith(str(allowed_base)):
            raise Forbidden("访问被拒绝")
        if not target.exists():
            raise FileNotFoundError("文件不存在")
        return target
