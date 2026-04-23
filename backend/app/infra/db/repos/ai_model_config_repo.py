from __future__ import annotations
from typing import Optional, List
from datetime import datetime

from sqlalchemy.orm import Session

from app.infra.db.models.ai_model_config import AIModelConfig


class AIModelConfigRepo:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, config_id: int) -> Optional[AIModelConfig]:
        return self._db.query(AIModelConfig).filter(AIModelConfig.id == config_id).first()

    def list_all(self, enabled_only: bool = False) -> List[AIModelConfig]:
        query = self._db.query(AIModelConfig).order_by(
            AIModelConfig.priority.asc(),
            AIModelConfig.created_at.desc()
        )
        if enabled_only:
            query = query.filter(AIModelConfig.is_enabled == True)
        return query.all()

    def list_by_usage(self, usage: str) -> List[AIModelConfig]:
        return (
            self._db.query(AIModelConfig)
            .filter(
                AIModelConfig.is_enabled == True,
                AIModelConfig.usage.in_([usage, "both"])
            )
            .order_by(AIModelConfig.priority.asc())
            .all()
        )

    def get_first_for_usage(self, usage: str) -> Optional[AIModelConfig]:
        models = self.list_by_usage(usage)
        return models[0] if models else None

    def create(self, data: dict, created_by: int) -> AIModelConfig:
        entity = AIModelConfig(
            name=data["name"],
            provider=data.get("provider", "custom"),
            model_id=data.get("model_id", data["name"]),
            api_key=data["api_key"],
            base_url=data["base_url"],
            usage=data.get("usage", "chat"),
            is_enabled=data.get("is_enabled", True),
            priority=data.get("priority", 0),
            description=data.get("description"),
            created_by=created_by,
        )
        self._db.add(entity)
        self._db.commit()
        self._db.refresh(entity)
        return entity

    def update(self, config_id: int, data: dict) -> Optional[AIModelConfig]:
        entity = self.get(config_id)
        if entity:
            for key in ["name", "provider", "model_id", "api_key", "base_url",
                        "usage", "is_enabled", "priority", "description"]:
                if key in data:
                    setattr(entity, key, data[key])
            self._db.commit()
            self._db.refresh(entity)
        return entity

    def delete(self, config_id: int) -> bool:
        entity = self.get(config_id)
        if entity:
            self._db.delete(entity)
            self._db.commit()
            return True
        return False

    def toggle(self, config_id: int) -> Optional[AIModelConfig]:
        entity = self.get(config_id)
        if entity:
            entity.is_enabled = not entity.is_enabled
            self._db.commit()
            self._db.refresh(entity)
        return entity