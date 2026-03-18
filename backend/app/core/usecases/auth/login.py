from app.core.ports.auth_provider import IAuthProvider
from app.core.strategies.auth_strategy import IAuthStrategy


class Login:
    def __init__(self, auth_strategy: IAuthStrategy, auth_provider: IAuthProvider) -> None:
        self._auth_strategy = auth_strategy
        self._auth_provider = auth_provider

    def execute(self, credentials: dict) -> dict:
        user = self._auth_strategy.authenticate(credentials)
        extra = self._auth_strategy.on_login_success(user)

        token = self._auth_provider.create_token(
            user.id, user.username, user.role, extra.get("session_token", ""))

        return {
            "access_token": token, "user": user,
            "expires_in": None,  # filled by route from settings
        }
