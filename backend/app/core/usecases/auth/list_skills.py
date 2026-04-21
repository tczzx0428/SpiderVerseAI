from __future__ import annotations
from app.core.entities.config import ConfigEntity
from app.core.ports.config_repo import IConfigRepo

SKILL_KEY_PREFIX = "skill:"

DEFAULT_SV_SPACE_SKILL = """\
---
name: sv-space
description: "Deploy Streamlit apps to SpiderVerseAI platform via sv CLI. Use when: user wants to build or deploy an app, use sv deploy/list/logs/stop, or manage SpiderVerseAI applications."
metadata: { "openclaw": { "emoji": "🚀", "requires": { "bins": ["pe"] } } }
---
# SpiderVerseAI Skill — 需求到上线全流程

请运行 `sv rules` 获取最新代码规范，然后根据用户需求用 Codex 生成代码，最后用 `sv deploy` 部署到平台。
"""


class ListSkills:
    def __init__(self, config_repo: IConfigRepo) -> None:
        self._config_repo = config_repo

    def execute(self) -> list[dict]:
        self._seed_defaults()
        rows = self._config_repo.get_by_prefix(SKILL_KEY_PREFIX)
        return [
            {"name": r.key[len(SKILL_KEY_PREFIX):], "content": r.value}
            for r in rows
        ]

    def _seed_defaults(self) -> None:
        key = f"{SKILL_KEY_PREFIX}sv-space"
        if not self._config_repo.get(key):
            self._config_repo.upsert(ConfigEntity(key=key, value=DEFAULT_SV_SPACE_SKILL))
