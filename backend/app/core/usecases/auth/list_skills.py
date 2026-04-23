from __future__ import annotations
from app.core.entities.config import ConfigEntity
from app.core.ports.config_repo import IConfigRepo

SKILL_KEY_PREFIX = "skill:"

DEFAULT_PT_SPACE_SKILL = """\
---
name: pt-space
description: "Deploy Streamlit apps to PulseTeach AI platform via pt CLI. Use when: user wants to build or deploy an app, use pt deploy/list/logs/stop, or manage PulseTeach AI applications."
metadata: { "openclaw": { "emoji": "🚀", "requires": { "bins": ["pe"] } } }
---
# PulseTeach AI Skill — 需求到上线全流程

请运行 `pt rules` 获取最新代码规范，然后根据用户需求用 Codex 生成代码，最后用 `pt deploy` 部署到平台。
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
        key = f"{SKILL_KEY_PREFIX}pt-space"
        if not self._config_repo.get(key):
            self._config_repo.upsert(ConfigEntity(key=key, value=DEFAULT_PT_SPACE_SKILL))
