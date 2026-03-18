from __future__ import annotations
from datetime import datetime
from typing import Optional

from app.core.entities.user import UserEntity
from app.core.errors import UsernameExists
from app.core.ports.auth_provider import IAuthProvider
from app.core.ports.user_repo import IUserRepo


class CreateUser:
    def __init__(self, user_repo: IUserRepo, auth_provider: IAuthProvider) -> None:
        self._user_repo = user_repo
        self._auth_provider = auth_provider

    def execute(self, username: str, password: str, email: Optional[str] = None,
                role: str = "user", expires_at: Optional[datetime] = None) -> UserEntity:
        if self._user_repo.get_by_username(username):
            raise UsernameExists(username)
        entity = UserEntity(
            id=0, username=username,
            hashed_pw=self._auth_provider.hash_password(password),
            email=email, role=role, expires_at=expires_at,
        )
        return self._user_repo.create(entity)


class BatchCreateUsers:
    def __init__(self, user_repo: IUserRepo, auth_provider: IAuthProvider) -> None:
        self._user_repo = user_repo
        self._auth_provider = auth_provider

    def execute(self, project_name: str, start_index: int, count: int,
                password: str, expires_at: Optional[datetime] = None) -> list[UserEntity]:
        hashed_pw = self._auth_provider.hash_password(password)
        created = []
        for i in range(count):
            idx = start_index + i
            username = f"{project_name}_{idx:03d}"
            if self._user_repo.get_by_username(username):
                raise UsernameExists(username)
            entity = UserEntity(
                id=0, username=username, hashed_pw=hashed_pw,
                role="annotator", expires_at=expires_at,
            )
            created.append(self._user_repo.create(entity))
        return created
