from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.core.entities.config import ConfigEntity, ConfigHistoryEntity
from app.infra.db.models.config import ConfigHistory, SystemConfig


def _to_entity(m: SystemConfig) -> ConfigEntity:
    return ConfigEntity(
        key=m.key, value=m.value,
        updated_by=m.updated_by, updated_at=m.updated_at,
    )


def _history_to_entity(m: ConfigHistory) -> ConfigHistoryEntity:
    return ConfigHistoryEntity(
        id=m.id, config_key=m.config_key, value=m.value,
        updated_by=m.updated_by, updater_name=m.updater_name,
        updated_at=m.updated_at,
    )


class SqlAlchemyConfigRepo:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, key: str) -> Optional[ConfigEntity]:
        m = self._db.query(SystemConfig).filter(SystemConfig.key == key).first()
        return _to_entity(m) if m else None

    def get_by_prefix(self, prefix: str) -> list[ConfigEntity]:
        models = self._db.query(SystemConfig).filter(
            SystemConfig.key.like(f"{prefix}%")
        ).all()
        return [_to_entity(m) for m in models]

    def upsert(self, entity: ConfigEntity) -> ConfigEntity:
        m = self._db.query(SystemConfig).filter(SystemConfig.key == entity.key).first()
        if m:
            m.value = entity.value
            m.updated_by = entity.updated_by
            m.updated_at = entity.updated_at or datetime.utcnow()
        else:
            m = SystemConfig(
                key=entity.key, value=entity.value,
                updated_by=entity.updated_by,
                updated_at=entity.updated_at or datetime.utcnow(),
            )
            self._db.add(m)
        self._db.commit()
        self._db.refresh(m)
        return _to_entity(m)

    def delete(self, key: str) -> bool:
        deleted = self._db.query(SystemConfig).filter(SystemConfig.key == key).delete()
        self._db.commit()
        return deleted > 0

    def add_history(self, entity: ConfigHistoryEntity) -> ConfigHistoryEntity:
        m = ConfigHistory(
            config_key=entity.config_key, value=entity.value,
            updated_by=entity.updated_by, updater_name=entity.updater_name,
            updated_at=entity.updated_at or datetime.utcnow(),
        )
        self._db.add(m)
        self._db.commit()
        self._db.refresh(m)
        return _history_to_entity(m)

    def get_history(self, key: str, limit: int = 20) -> list[ConfigHistoryEntity]:
        models = (
            self._db.query(ConfigHistory)
            .filter(ConfigHistory.config_key == key)
            .order_by(ConfigHistory.id.desc())
            .limit(limit)
            .all()
        )
        return [_history_to_entity(m) for m in models]

    def get_last_history(self, key: str) -> Optional[ConfigHistoryEntity]:
        m = (
            self._db.query(ConfigHistory)
            .filter(ConfigHistory.config_key == key)
            .order_by(ConfigHistory.id.desc())
            .first()
        )
        return _history_to_entity(m) if m else None
