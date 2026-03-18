from __future__ import annotations
from datetime import datetime

from app.core.entities.config import ConfigEntity, ConfigHistoryEntity
from app.core.errors import SkillNotFound
from app.core.ports.config_repo import IConfigRepo
from app.core.usecases.auth.list_skills import SKILL_KEY_PREFIX


class UpsertSkill:
    def __init__(self, config_repo: IConfigRepo) -> None:
        self._config_repo = config_repo

    def execute(self, name: str, content: str, admin_id: int, admin_username: str) -> dict:
        key = f"{SKILL_KEY_PREFIX}{name}"
        now = datetime.utcnow()
        self._config_repo.upsert(ConfigEntity(
            key=key, value=content, updated_by=admin_id, updated_at=now))
        self._config_repo.add_history(ConfigHistoryEntity(
            id=0, config_key=key, value=content,
            updated_by=admin_id, updater_name=admin_username, updated_at=now))
        return {"ok": True, "name": name}


class DeleteSkill:
    def __init__(self, config_repo: IConfigRepo) -> None:
        self._config_repo = config_repo

    def execute(self, name: str) -> None:
        key = f"{SKILL_KEY_PREFIX}{name}"
        if not self._config_repo.delete(key):
            raise SkillNotFound(name)


class ListSkillsAdmin:
    def __init__(self, config_repo: IConfigRepo) -> None:
        self._config_repo = config_repo

    def execute(self) -> list[dict]:
        from app.core.usecases.auth.list_skills import ListSkills
        # Seed defaults
        ls = ListSkills(self._config_repo)
        ls._seed_defaults()

        rows = self._config_repo.get_by_prefix(SKILL_KEY_PREFIX)
        return [
            {"name": r.key[len(SKILL_KEY_PREFIX):], "content": r.value, "updated_at": r.updated_at}
            for r in rows
        ]
