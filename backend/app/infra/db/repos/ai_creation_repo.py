from __future__ import annotations
from typing import Optional
from datetime import datetime

from sqlalchemy.orm import Session

from app.infra.db.models.ai_creation import AICreation


class AICreationRepo:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, creation_id: int) -> Optional[AICreation]:
        return self._db.query(AICreation).filter(AICreation.id == creation_id).first()

    def list_by_user(self, user_id: int, limit: int = 20) -> list[AICreation]:
        return (
            self._db.query(AICreation)
            .filter(AICreation.user_id == user_id)
            .order_by(AICreation.created_at.desc())
            .limit(limit)
            .all()
        )

    def create(self, user_id: int, title: str = None) -> AICreation:
        entity = AICreation(
            user_id=user_id,
            title=title,
            status="chatting",
            conversation=[],
            progress=0,
        )
        self._db.add(entity)
        self._db.commit()
        self._db.refresh(entity)
        return entity

    def update_conversation(self, creation_id: int, conversation: list) -> AICreation:
        entity = self.get(creation_id)
        if entity:
            entity.conversation = conversation
            self._db.commit()
            self._db.refresh(entity)
        return entity

    def update_status(self, creation_id: int, status: str,
                      progress: int = None, message: str = None,
                      error: str = None, generated_code: dict = None,
                      app_id: int = None) -> AICreation:
        entity = self.get(creation_id)
        if entity:
            entity.status = status
            if progress is not None:
                entity.progress = progress
            if message is not None:
                entity.progress_message = message
            if error is not None:
                entity.error_message = error
            if generated_code is not None:
                entity.generated_code = generated_code
            if app_id is not None:
                entity.app_id = app_id
            self._db.commit()
            self._db.refresh(entity)
        return entity

    def delete(self, creation_id: int) -> None:
        entity = self.get(creation_id)
        if entity:
            self._db.delete(entity)
            self._db.commit()