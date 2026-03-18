from __future__ import annotations
from datetime import datetime

from app.core.entities.config import ConfigEntity, ConfigHistoryEntity
from app.core.ports.config_repo import IConfigRepo

TEMPLATE_KEY = "code_rule_prompt"


class GetTemplate:
    def __init__(self, config_repo: IConfigRepo, default_template: str) -> None:
        self._config_repo = config_repo
        self._default_template = default_template

    def execute(self) -> dict:
        cfg = self._get_or_create()
        last = self._config_repo.get_last_history(TEMPLATE_KEY)
        return {
            "key": cfg.key, "value": cfg.value,
            "updated_by": cfg.updated_by,
            "updater_name": last.updater_name if last else None,
            "updated_at": cfg.updated_at,
        }

    def _get_or_create(self) -> ConfigEntity:
        cfg = self._config_repo.get(TEMPLATE_KEY)
        if not cfg:
            cfg = self._config_repo.upsert(
                ConfigEntity(key=TEMPLATE_KEY, value=self._default_template))
        return cfg


class UpdateTemplate:
    def __init__(self, config_repo: IConfigRepo, default_template: str) -> None:
        self._config_repo = config_repo
        self._default_template = default_template

    def execute(self, value: str, admin_id: int, admin_username: str) -> dict:
        now = datetime.utcnow()

        # Ensure exists
        cfg = self._config_repo.get(TEMPLATE_KEY)
        if not cfg:
            cfg = ConfigEntity(key=TEMPLATE_KEY, value=self._default_template)

        cfg.value = value
        cfg.updated_by = admin_id
        cfg.updated_at = now
        updated = self._config_repo.upsert(cfg)

        self._config_repo.add_history(ConfigHistoryEntity(
            id=0, config_key=TEMPLATE_KEY, value=value,
            updated_by=admin_id, updater_name=admin_username, updated_at=now))

        return {
            "key": updated.key, "value": updated.value,
            "updated_by": updated.updated_by,
            "updater_name": admin_username,
            "updated_at": updated.updated_at,
        }


class GetTemplateHistory:
    def __init__(self, config_repo: IConfigRepo) -> None:
        self._config_repo = config_repo

    def execute(self) -> list:
        entities = self._config_repo.get_history(TEMPLATE_KEY, limit=20)
        return [
            {
                "id": e.id, "config_key": e.config_key, "value": e.value,
                "updater_name": e.updater_name, "updated_at": e.updated_at,
            }
            for e in entities
        ]
