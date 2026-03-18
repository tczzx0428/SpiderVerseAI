from __future__ import annotations
from typing import Optional, Protocol

from app.core.entities.user import UserEntity


class IAuthStrategy(Protocol):
    strategy_name: str

    def authenticate(self, credentials: dict) -> Optional[UserEntity]: ...
    def on_login_success(self, user: UserEntity) -> dict: ...


class AuthStrategyRegistry:
    def __init__(self) -> None:
        self._strategies: dict[str, IAuthStrategy] = {}

    def register(self, strategy: IAuthStrategy) -> None:
        self._strategies[strategy.strategy_name] = strategy

    def get(self, name: str) -> IAuthStrategy:
        s = self._strategies.get(name)
        if not s:
            raise ValueError(f"未知的认证方式: {name}")
        return s
