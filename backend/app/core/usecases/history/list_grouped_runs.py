from __future__ import annotations
import json
import logging
from datetime import datetime
from pathlib import Path

from app.config import settings
from app.core.ports.app_repo import IAppRepo
from app.core.shared.batch_grouping import group_by_batch, scan_data_dir
from app.core.shared.time_utils import CST

logger = logging.getLogger(__name__)


class ListGroupedRuns:
    def __init__(self, app_repo: IAppRepo) -> None:
        self._app_repo = app_repo

    def execute(self, current_user_id: int, current_user_role: str) -> dict:
        apps = self._app_repo.list_all()
        all_groups: list[dict] = []

        for app in apps:
            if current_user_role != "admin" and app.owner_id != current_user_id:
                continue

            data_dir = Path(settings.upload_dir) / str(app.id) / "data"
            raw_files, batch_ts_set = scan_data_dir(data_dir)
            ts_files = group_by_batch(raw_files, batch_ts_set)

            # Read history/*.json metadata
            history_dir = data_dir / "history"
            run_meta: dict[str, dict] = {}
            if history_dir.exists():
                for f in history_dir.glob("*.json"):
                    try:
                        record = json.loads(f.read_text(encoding="utf-8"))
                        rid = record.get("run_id", "")
                        from app.core.shared.batch_grouping import extract_timestamp
                        ts_key = extract_timestamp(rid) or rid
                        run_meta[ts_key] = record
                    except Exception:
                        continue

            # Read _tracking records for username matching
            tracking_dir = data_dir / "history" / "_tracking"
            tracking_records: list[dict] = []
            if tracking_dir.exists():
                for f in tracking_dir.iterdir():
                    if not f.is_file() or not f.name.endswith(".json"):
                        continue
                    try:
                        record = json.loads(f.read_text(encoding="utf-8"))
                        uname = record.get("username", "")
                        if uname and uname != "anonymous":
                            tracking_records.append(record)
                    except Exception:
                        continue
                tracking_records.sort(key=lambda r: r.get("timestamp", ""))

            for ts_key, files in ts_files.items():
                meta = run_meta.get(ts_key, {})
                try:
                    dt = datetime.strptime(ts_key, "%Y%m%d_%H%M%S").replace(tzinfo=CST)
                    timestamp = dt.isoformat()
                except ValueError:
                    timestamp = meta.get("timestamp", "")

                username = meta.get("username", "")
                summary = meta.get("summary", "")

                # Match username from tracking records
                if not username and tracking_records:
                    try:
                        group_dt = datetime.strptime(ts_key, "%Y%m%d_%H%M%S")
                    except ValueError:
                        group_dt = None
                    if group_dt:
                        best_user = ""
                        best_delta = None
                        for tr in tracking_records:
                            try:
                                tr_dt = datetime.fromisoformat(
                                    tr["timestamp"].replace("+08:00", "").replace("Z", ""))
                            except Exception:
                                continue
                            delta = abs((tr_dt - group_dt).total_seconds())
                            if delta <= 1800 and (best_delta is None or delta < best_delta):
                                best_user = tr.get("username", "")
                                best_delta = delta
                        username = best_user

                if not summary:
                    result_files = [f for f in files if f.get("category") == "result"]
                    if result_files:
                        summary = result_files[0]["name"]
                    elif files:
                        summary = files[0]["name"]

                # Backfill metadata
                if ts_key not in run_meta and (username or summary):
                    try:
                        meta_path = history_dir / f"{ts_key}.json"
                        if not meta_path.exists():
                            history_dir.mkdir(parents=True, exist_ok=True)
                            backfill = {
                                "run_id": ts_key, "username": username,
                                "timestamp": timestamp, "summary": summary,
                            }
                            meta_path.write_text(
                                json.dumps(backfill, ensure_ascii=False), encoding="utf-8")
                    except Exception:
                        pass

                all_groups.append({
                    "ts_key": ts_key, "app_id": app.id,
                    "app_name": app.name, "app_slug": app.slug,
                    "timestamp": timestamp,
                    "username": username if username != "anonymous" else "",
                    "summary": summary,
                    "files": sorted(files, key=lambda x: x["name"]),
                })

        all_groups.sort(key=lambda x: x["timestamp"], reverse=True)
        return {"groups": all_groups[:200]}
