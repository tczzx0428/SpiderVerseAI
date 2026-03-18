from __future__ import annotations
from typing import Optional

from sqlalchemy.orm import Session

from app.core.entities.user import UserEntity
from app.infra.db.models.user import User


def _to_entity(m: User) -> UserEntity:
    return UserEntity(
        id=m.id, username=m.username, hashed_pw=m.hashed_pw,
        role=m.role, email=m.email, is_active=m.is_active,
        session_token=m.session_token, expires_at=m.expires_at,
        created_at=m.created_at, updated_at=m.updated_at,
    )


def _apply_entity(m: User, e: UserEntity) -> None:
    m.username = e.username
    m.email = e.email
    m.hashed_pw = e.hashed_pw
    m.role = e.role
    m.is_active = e.is_active
    m.session_token = e.session_token
    m.expires_at = e.expires_at


class SqlAlchemyUserRepo:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, user_id: int) -> Optional[UserEntity]:
        m = self._db.query(User).filter(User.id == user_id).first()
        return _to_entity(m) if m else None

    def get_by_username(self, username: str) -> Optional[UserEntity]:
        m = self._db.query(User).filter(User.username == username).first()
        return _to_entity(m) if m else None

    def get_batch(self, user_ids: list[int]) -> dict[int, UserEntity]:
        if not user_ids:
            return {}
        models = self._db.query(User).filter(User.id.in_(user_ids)).all()
        return {m.id: _to_entity(m) for m in models}

    def list_all(self) -> list[UserEntity]:
        return [_to_entity(m) for m in self._db.query(User).order_by(User.id).all()]

    def create(self, entity: UserEntity) -> UserEntity:
        m = User(
            username=entity.username, email=entity.email,
            hashed_pw=entity.hashed_pw, role=entity.role,
            expires_at=entity.expires_at,
        )
        self._db.add(m)
        self._db.commit()
        self._db.refresh(m)
        return _to_entity(m)

    def update(self, entity: UserEntity) -> UserEntity:
        m = self._db.query(User).filter(User.id == entity.id).first()
        if m:
            _apply_entity(m, entity)
            self._db.commit()
            self._db.refresh(m)
            return _to_entity(m)
        raise ValueError(f"User {entity.id} not found")

    def delete(self, user_id: int) -> None:
        m = self._db.query(User).filter(User.id == user_id).first()
        if m:
            self._db.delete(m)
            self._db.commit()

    def count(self) -> int:
        return self._db.query(User).count()
