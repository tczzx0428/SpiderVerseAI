from __future__ import annotations
from app.core.ports.auth_provider import IAuthProvider


class VerifyAppAccess:
    def __init__(self, auth_provider: IAuthProvider) -> None:
        self._auth_provider = auth_provider

    def execute(self, token: str | None) -> dict | None:
        if not token:
            return None
        payload = self._auth_provider.decode_token(token)
        if not payload:
            return None
        return {
            "username": payload.get("username", ""),
            "role": payload.get("role", "user"),
            "user_id": int(payload.get("sub", 0)),
        }
