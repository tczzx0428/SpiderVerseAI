from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path

from app.config import settings
from app.core.ports.app_repo import IAppRepo
from app.core.ports.user_repo import IUserRepo
from app.core.shared.batch_grouping import count_run_groups, extract_timestamp


class GetStats:
    def __init__(self, app_repo: IAppRepo, user_repo: IUserRepo) -> None:
        self._app_repo = app_repo
        self._user_repo = user_repo

    def execute(self) -> dict:
        apps = self._app_repo.list_all()
        users = self._user_repo.list_all()

        # Load tracking views
        views = self._load_tracking(apps)

        # Collect runs using shared batch_grouping
        app_run_count, app_run_users, user_app_runs = self._collect_runs(apps)

        # Per-app view stats
        app_view_count: dict[int, int] = defaultdict(int)
        app_view_users: dict[int, set] = defaultdict(set)
        for v in views:
            aid = v.get("app_id")
            uname = v.get("username", "anonymous")
            app_view_count[aid] += 1
            if uname != "anonymous":
                app_view_users[aid].add(uname)

        # Per-user stats
        user_upload: dict[int, int] = defaultdict(int)
        for app in apps:
            user_upload[app.owner_id] += 1

        user_view_count: dict[str, int] = defaultdict(int)
        user_run_count: dict[str, int] = defaultdict(int)
        for v in views:
            user_view_count[v.get("username", "anonymous")] += 1
        for uname, app_map in user_app_runs.items():
            user_run_count[uname] = sum(app_map.values())

        # User x App detail
        user_app_detail: dict[str, dict[int, dict]] = defaultdict(
            lambda: defaultdict(lambda: {"view": 0, "run": 0}))
        for v in views:
            uname = v.get("username", "anonymous")
            if uname == "anonymous":
                continue
            user_app_detail[uname][v.get("app_id")]["view"] += 1
        for uname, app_map in user_app_runs.items():
            for aid, cnt in app_map.items():
                user_app_detail[uname][aid]["run"] += cnt

        # Assemble
        owner_map = {u.id: u.username for u in users}
        app_name_map = {a.id: a.name for a in apps}

        apps_stats = [
            {
                "id": a.id, "name": a.name, "slug": a.slug, "status": a.status,
                "owner": owner_map.get(a.owner_id, ""), "created_at": a.created_at,
                "view_count": app_view_count[a.id], "view_users": len(app_view_users[a.id]),
                "run_count": app_run_count[a.id], "run_users": len(app_run_users[a.id]),
            }
            for a in sorted(apps, key=lambda a: (app_run_count[a.id], app_view_count[a.id]), reverse=True)
        ]

        users_stats = [
            {
                "id": u.id, "username": u.username, "role": u.role, "is_active": u.is_active,
                "upload_count": user_upload[u.id],
                "view_count": user_view_count[u.username],
                "run_count": user_run_count.get(u.username, 0),
            }
            for u in sorted(users, key=lambda u: user_view_count[u.username] + user_run_count.get(u.username, 0), reverse=True)
        ]

        usage_detail = []
        for uname, app_map in user_app_detail.items():
            for aid, counts in app_map.items():
                usage_detail.append({
                    "username": uname, "app_id": aid,
                    "app_name": app_name_map.get(aid, f"App#{aid}"),
                    "view_count": counts["view"], "run_count": counts["run"],
                })
        usage_detail.sort(key=lambda x: x["view_count"] + x["run_count"], reverse=True)

        return {"apps": apps_stats, "users": users_stats, "usage_detail": usage_detail}

    def _load_tracking(self, apps) -> list[dict]:
        views = []
        for app in apps:
            tracking_dir = Path(settings.upload_dir) / str(app.id) / "data" / "history" / "_tracking"
            if not tracking_dir.exists():
                continue
            for f in tracking_dir.glob("*.json"):
                try:
                    record = json.loads(f.read_text(encoding="utf-8"))
                    record.setdefault("app_id", app.id)
                    record.setdefault("app_name", app.name)
                    views.append(record)
                except Exception:
                    continue
        return views

    def _collect_runs(self, apps) -> tuple:
        app_run_count: dict[int, int] = defaultdict(int)
        app_run_users: dict[int, set] = defaultdict(set)
        user_app_runs: dict[str, dict[int, int]] = defaultdict(lambda: defaultdict(int))

        for app in apps:
            data_dir = Path(settings.upload_dir) / str(app.id) / "data"
            num_groups, final_groups = count_run_groups(data_dir)
            app_run_count[app.id] = num_groups

            # Read history metadata for username matching
            history_dir = data_dir / "history"
            meta_map: dict[str, str] = {}
            if history_dir.exists():
                for f in history_dir.glob("*.json"):
                    try:
                        record = json.loads(f.read_text(encoding="utf-8"))
                        rid = record.get("run_id", "")
                        ts = extract_timestamp(rid) or rid
                        uname = record.get("username", "")
                        if uname and uname != "anonymous":
                            meta_map[ts] = uname
                    except Exception:
                        continue

            for ts_key in final_groups:
                uname = meta_map.get(ts_key, "")
                if uname:
                    app_run_users[app.id].add(uname)
                    user_app_runs[uname][app.id] += 1

        return app_run_count, app_run_users, user_app_runs
