from __future__ import annotations
from typing import Optional

from sqlalchemy.orm import Session

from app.core.entities.prompt import PromptEntity
from app.infra.db.models.prompt import Prompt


def _to_entity(m: Prompt) -> PromptEntity:
    return PromptEntity(
        id=m.id, title=m.title, content=m.content,
        category=m.category, sort_order=m.sort_order,
        is_active=m.is_active, created_by=m.created_by,
        created_at=m.created_at, updated_at=m.updated_at,
    )


class SqlAlchemyPromptRepo:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list(self, category: Optional[str] = None, active_only: bool = True) -> list[PromptEntity]:
        query = self._db.query(Prompt)
        if active_only:
            query = query.filter(Prompt.is_active == True)
        if category:
            query = query.filter(Prompt.category == category)
        return [_to_entity(m) for m in query.order_by(Prompt.sort_order, Prompt.id).all()]

    def list_categories(self) -> list[str]:
        rows = self._db.query(Prompt.category).filter(
            Prompt.is_active == True, Prompt.category != None
        ).distinct().all()
        return [r[0] for r in rows if r[0]]

    def get(self, prompt_id: int) -> Optional[PromptEntity]:
        m = self._db.query(Prompt).filter(Prompt.id == prompt_id).first()
        return _to_entity(m) if m else None

    def create(self, entity: PromptEntity) -> PromptEntity:
        m = Prompt(
            title=entity.title, content=entity.content,
            category=entity.category, sort_order=entity.sort_order,
            created_by=entity.created_by,
        )
        self._db.add(m)
        self._db.commit()
        self._db.refresh(m)
        return _to_entity(m)

    def update(self, entity: PromptEntity) -> PromptEntity:
        m = self._db.query(Prompt).filter(Prompt.id == entity.id).first()
        if m:
            m.title = entity.title
            m.content = entity.content
            m.category = entity.category
            m.sort_order = entity.sort_order
            m.is_active = entity.is_active
            self._db.commit()
            self._db.refresh(m)
            return _to_entity(m)
        raise ValueError(f"Prompt {entity.id} not found")

    def delete(self, prompt_id: int) -> None:
        m = self._db.query(Prompt).filter(Prompt.id == prompt_id).first()
        if m:
            self._db.delete(m)
            self._db.commit()
