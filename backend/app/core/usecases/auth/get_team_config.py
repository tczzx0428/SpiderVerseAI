from __future__ import annotations

from app.config import settings
from app.core.entities.config import ConfigEntity
from app.core.ports.config_repo import IConfigRepo

TEAM_KEY_PREFIX = "team:"

_TEAM_FIELDS = {
    "api_key":        lambda: settings.team_api_key,
    "base_url":       lambda: settings.team_base_url,
    "codex_model":    lambda: settings.codex_model,
    "openclaw_model": lambda: settings.openclaw_model,
}


class GetTeamConfig:
    def __init__(self, config_repo: IConfigRepo) -> None:
        self._config_repo = config_repo

    def execute(self) -> dict:
        self._seed_defaults()
        return {
            field: self._config_repo.get(f"{TEAM_KEY_PREFIX}{field}").value
            for field in _TEAM_FIELDS
        }

    def _seed_defaults(self) -> None:
        for field, get_default in _TEAM_FIELDS.items():
            key = f"{TEAM_KEY_PREFIX}{field}"
            if not self._config_repo.get(key):
                self._config_repo.upsert(ConfigEntity(key=key, value=get_default()))
