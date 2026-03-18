from __future__ import annotations
from typing import Optional

from app.core.entities.user import UserEntity
from app.core.errors import CannotDeleteSelf, UserNotFound
from app.core.ports.user_repo import IUserRepo


class UpdateUser:
    def __init__(self, user_repo: IUserRepo) -> None:
        self._user_repo = user_repo

    def execute(self, user_id: int, **kwargs) -> UserEntity:
        user = self._user_repo.get(user_id)
        if not user:
            raise UserNotFound(user_id=user_id)
        for k, v in kwargs.items():
            if v is not None:
                setattr(user, k, v)
        return self._user_repo.update(user)


class DeleteUser:
    def __init__(self, user_repo: IUserRepo) -> None:
        self._user_repo = user_repo

    def execute(self, user_id: int, admin_id: int) -> None:
        if user_id == admin_id:
            raise CannotDeleteSelf()
        user = self._user_repo.get(user_id)
        if not user:
            raise UserNotFound(user_id=user_id)
        self._user_repo.delete(user_id)
