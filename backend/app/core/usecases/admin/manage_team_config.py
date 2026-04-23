from __future__ import annotations
from datetime import datetime

from app.core.entities.config import ConfigEntity, ConfigHistoryEntity
from app.core.ports.config_repo import IConfigRepo
from app.core.usecases.auth.get_team_config import TEAM_KEY_PREFIX

ALLOWED_FIELDS = {"api_key", "base_url", "codex_model", "openclaw_model",
                  "ai_api_key", "ai_base_url", "ai_model", "ai_code_model"}


class UpdateTeamConfig:
    def __init__(self, config_repo: IConfigRepo) -> None:
        self._config_repo = config_repo

    def execute(self, updates: dict, admin_id: int, admin_username: str) -> dict:
        now = datetime.utcnow()
        changed = []
        for field, value in updates.items():
            if field not in ALLOWED_FIELDS:
                continue
            key = f"{TEAM_KEY_PREFIX}{field}"
            self._config_repo.upsert(ConfigEntity(
                key=key, value=value, updated_by=admin_id, updated_at=now))
            self._config_repo.add_history(ConfigHistoryEntity(
                id=0, config_key=key, value=value,
                updated_by=admin_id, updater_name=admin_username, updated_at=now))
            changed.append(field)
        return {"ok": True, "updated": changed}
