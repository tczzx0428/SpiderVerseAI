from __future__ import annotations
from typing import Optional

from sqlalchemy.orm import Session

from app.core.entities.app import AppEntity
from app.infra.db.models.app import App


def _to_entity(m: App) -> AppEntity:
    return AppEntity(
        id=m.id, name=m.name, slug=m.slug, description=m.description,
        owner_id=m.owner_id, status=m.status,
        container_id=m.container_id, container_name=m.container_name,
        host_port=m.host_port, upload_path=m.upload_path, build_log=m.build_log,
        created_at=m.created_at, updated_at=m.updated_at,
    )


def _apply_entity(m: App, e: AppEntity) -> None:
    m.name = e.name
    m.slug = e.slug
    m.description = e.description
    m.owner_id = e.owner_id
    m.status = e.status
    m.container_id = e.container_id
    m.container_name = e.container_name
    m.host_port = e.host_port
    m.upload_path = e.upload_path
    m.build_log = e.build_log


class SqlAlchemyAppRepo:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, app_id: int) -> Optional[AppEntity]:
        m = self._db.query(App).filter(App.id == app_id).first()
        return _to_entity(m) if m else None

    def get_by_slug(self, slug: str) -> Optional[AppEntity]:
        m = self._db.query(App).filter(App.slug == slug).first()
        return _to_entity(m) if m else None

    def list(self, page: int = 1, size: int = 20, status: Optional[str] = None) -> tuple[list[AppEntity], int]:
        query = self._db.query(App)
        if status:
            query = query.filter(App.status == status)
        total = query.count()
        models = query.order_by(App.created_at.desc()).offset((page - 1) * size).limit(size).all()
        return [_to_entity(m) for m in models], total

    def list_all(self) -> list[AppEntity]:
        return [_to_entity(m) for m in self._db.query(App).all()]

    def create(self, entity: AppEntity) -> AppEntity:
        m = App(
            name=entity.name, slug=entity.slug, description=entity.description,
            owner_id=entity.owner_id, status=entity.status,
        )
        self._db.add(m)
        self._db.commit()
        self._db.refresh(m)
        return _to_entity(m)

    def update(self, entity: AppEntity) -> AppEntity:
        m = self._db.query(App).filter(App.id == entity.id).first()
        if m:
            _apply_entity(m, entity)
            self._db.commit()
            self._db.refresh(m)
            return _to_entity(m)
        raise ValueError(f"App {entity.id} not found")

    def delete(self, app_id: int) -> None:
        m = self._db.query(App).filter(App.id == app_id).first()
        if m:
            self._db.delete(m)
            self._db.commit()

    def count(self, status: Optional[str] = None) -> int:
        query = self._db.query(App)
        if status:
            query = query.filter(App.status == status)
        return query.count()
