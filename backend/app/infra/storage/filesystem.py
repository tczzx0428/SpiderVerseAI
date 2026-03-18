from __future__ import annotations
import json
import os
import shutil
import zipfile
from pathlib import Path


class LocalFileStorage:
    def read_json_files(self, directory: Path, pattern: str = "*.json") -> list[dict]:
        if not directory.exists():
            return []
        results = []
        for f in directory.glob(pattern):
            try:
                results.append(json.loads(f.read_text(encoding="utf-8")))
            except Exception:
                continue
        return results

    def write_json(self, path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def read_json(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def list_files(self, directory: Path, recursive: bool = False) -> list[Path]:
        if not directory.exists():
            return []
        if recursive:
            return [f for f in directory.rglob("*") if f.is_file() and not f.name.startswith(".")]
        return [f for f in directory.iterdir() if f.is_file() and not f.name.startswith(".")]

    def ensure_dir(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)

    def remove_tree(self, path: Path) -> None:
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)

    def file_exists(self, path: Path) -> bool:
        return path.exists()

    def file_stat(self, path: Path) -> dict:
        stat = path.stat()
        return {"size": stat.st_size, "mtime": stat.st_mtime}

    def safe_extract_zip(self, zip_path: str, extract_to: str) -> None:
        extract_to_path = Path(extract_to).resolve()
        with zipfile.ZipFile(zip_path, "r") as zf:
            for info in zf.infolist():
                if info.external_attr >> 16 & 0o120000 == 0o120000:
                    raise ValueError(f"Zip contains symlink, rejected: {info.filename}")
                target = (extract_to_path / info.filename).resolve()
                if not str(target).startswith(str(extract_to_path)):
                    raise ValueError(f"Unsafe path in zip: {info.filename}")
            zf.extractall(extract_to)

    def validate_zip_structure(self, zip_path: str, required: set[str] | None = None) -> tuple[bool, str]:
        if required is None:
            required = {"app.py", "requirements.txt"}
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                names = set(zf.namelist())
                flat_names = {os.path.basename(n) for n in names}
                missing = required - flat_names
                if missing:
                    return False, f"缺少必要文件: {', '.join(missing)}"
        except zipfile.BadZipFile:
            return False, "不是有效的 zip 文件"
        return True, ""
