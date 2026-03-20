from __future__ import annotations
import json
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.core.entities.skill import SkillEntity
from app.infra.db.models.config import SystemConfig

SKILL_KEY_PREFIX = "skill:"


def _parse_skill(m: SystemConfig) -> SkillEntity:
    """Parse a SystemConfig row into a SkillEntity.
    Supports both legacy (plain markdown) and new (JSON) formats.
    """
    name = m.key[len(SKILL_KEY_PREFIX):]
    try:
        data = json.loads(m.value)
        return SkillEntity(
            name=name,
            content=data.get("content", ""),
            description=data.get("description", ""),
            category=data.get("category", "other"),
            author_id=data.get("author_id"),
            author_name=data.get("author_name", ""),
            installs=data.get("installs", 0),
            pinned=data.get("pinned", False),
            version=data.get("version", "1.0.0"),
            changelog=data.get("changelog", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else m.updated_at,
            updated_at=m.updated_at,
        )
    except (json.JSONDecodeError, TypeError):
        # Legacy format: plain markdown content
        return SkillEntity(
            name=name,
            content=m.value,
            description="",
            category="other",
            author_id=m.updated_by,
            author_name="",
            installs=0,
            pinned=False,
            created_at=m.updated_at,
            updated_at=m.updated_at,
        )


def _serialize_skill(entity: SkillEntity) -> str:
    return json.dumps({
        "content": entity.content,
        "description": entity.description,
        "category": entity.category,
        "author_id": entity.author_id,
        "author_name": entity.author_name,
        "installs": entity.installs,
        "pinned": entity.pinned,
        "version": entity.version,
        "changelog": entity.changelog,
        "created_at": entity.created_at.isoformat() if entity.created_at else None,
    }, ensure_ascii=False)


class SkillRepo:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_all(self) -> list[SkillEntity]:
        models = self._db.query(SystemConfig).filter(
            SystemConfig.key.like(f"{SKILL_KEY_PREFIX}%")
        ).all()
        return [_parse_skill(m) for m in models]

    def get(self, name: str) -> Optional[SkillEntity]:
        m = self._db.query(SystemConfig).filter(
            SystemConfig.key == f"{SKILL_KEY_PREFIX}{name}"
        ).first()
        return _parse_skill(m) if m else None

    def upsert(self, entity: SkillEntity) -> SkillEntity:
        key = f"{SKILL_KEY_PREFIX}{entity.name}"
        now = datetime.utcnow()
        m = self._db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if m:
            entity.updated_at = now
            # Preserve created_at from existing
            existing = _parse_skill(m)
            if not entity.created_at:
                entity.created_at = existing.created_at
            m.value = _serialize_skill(entity)
            m.updated_by = entity.author_id
            m.updated_at = now
        else:
            entity.created_at = entity.created_at or now
            entity.updated_at = now
            m = SystemConfig(
                key=key,
                value=_serialize_skill(entity),
                updated_by=entity.author_id,
                updated_at=now,
            )
            self._db.add(m)
        self._db.commit()
        self._db.refresh(m)
        return _parse_skill(m)

    def delete(self, name: str) -> bool:
        deleted = self._db.query(SystemConfig).filter(
            SystemConfig.key == f"{SKILL_KEY_PREFIX}{name}"
        ).delete()
        self._db.commit()
        return deleted > 0

    def increment_installs(self, name: str) -> bool:
        m = self._db.query(SystemConfig).filter(
            SystemConfig.key == f"{SKILL_KEY_PREFIX}{name}"
        ).first()
        if not m:
            return False
        entity = _parse_skill(m)
        entity.installs += 1
        m.value = _serialize_skill(entity)
        self._db.commit()
        return True
