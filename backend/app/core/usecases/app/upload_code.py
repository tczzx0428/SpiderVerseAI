from __future__ import annotations
import shutil
from pathlib import Path

from app.config import settings
from app.core.errors import AppNotFound, Forbidden, InvalidFile
from app.core.ports.app_repo import IAppRepo
from app.infra.storage.filesystem import LocalFileStorage


class UploadCode:
    def __init__(self, app_repo: IAppRepo, storage: LocalFileStorage) -> None:
        self._app_repo = app_repo
        self._storage = storage

    def execute(self, app_id: int, zip_path: str, current_user_id: int,
                current_user_role: str) -> dict:
        app = self._app_repo.get(app_id)
        if not app:
            raise AppNotFound(app_id=app_id)
        if current_user_role != "admin" and app.owner_id != current_user_id:
            raise Forbidden()

        ok, msg = self._storage.validate_zip_structure(zip_path)
        if not ok:
            raise InvalidFile(msg)

        extract_path = self._extract_upload(zip_path, app_id)
        app.upload_path = extract_path
        app.status = "pending"

        # Auto-read README.md as description
        readme_path = Path(extract_path) / "README.md"
        if readme_path.exists():
            try:
                app.description = readme_path.read_text(encoding="utf-8")
            except Exception:
                pass

        self._app_repo.update(app)
        return {"message": "上传成功", "app_id": app_id, "upload_path": extract_path}

    def _extract_upload(self, zip_path: str, app_id: int) -> str:
        extract_to = Path(settings.upload_dir) / str(app_id)
        data_dir = extract_to / "data"
        tmp_data = Path(settings.upload_dir) / f".data_backup_{app_id}"

        if data_dir.exists():
            shutil.move(str(data_dir), str(tmp_data))

        if extract_to.exists():
            shutil.rmtree(extract_to)
        extract_to.mkdir(parents=True, exist_ok=True)

        self._storage.safe_extract_zip(zip_path, str(extract_to))

        if tmp_data.exists():
            shutil.move(str(tmp_data), str(data_dir))
        else:
            data_dir.mkdir(parents=True, exist_ok=True)

        version_file = data_dir / ".deploy_version"
        current = int(version_file.read_text().strip()) if version_file.exists() else 0
        version_file.write_text(str(current + 1))

        for depth in range(3):
            pattern = "/".join(["*"] * (depth + 1)) + "/app.py"
            matches = list(extract_to.glob(pattern))
            if matches:
                return str(matches[0].parent)

        return str(extract_to)
