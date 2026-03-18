from __future__ import annotations
import uuid
from typing import Optional

from app.core.entities.user import UserEntity
from app.core.errors import AccountDisabled, InvalidPassword
from app.core.ports.auth_provider import IAuthProvider
from app.core.ports.user_repo import IUserRepo


class PasswordAuth:
    strategy_name: str = "password"

    def __init__(self, user_repo: IUserRepo, auth_provider: IAuthProvider) -> None:
        self._user_repo = user_repo
        self._auth_provider = auth_provider

    def authenticate(self, credentials: dict) -> Optional[UserEntity]:
        username = credentials.get("username", "")
        password = credentials.get("password", "")

        user = self._user_repo.get_by_username(username)
        if not user or not self._auth_provider.verify_password(password, user.hashed_pw):
            raise InvalidPassword()
        if not user.is_active:
            raise AccountDisabled()
        return user

    def on_login_success(self, user: UserEntity) -> dict:
        new_sid = uuid.uuid4().hex[:16]
        user.session_token = new_sid
        self._user_repo.update(user)
        return {"session_token": new_sid}
