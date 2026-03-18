from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class JwtAuthProvider:
    def hash_password(self, password: str) -> str:
        return _pwd_context.hash(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        return _pwd_context.verify(plain, hashed)

    def create_token(self, user_id: int, username: str, role: str, session_token: str = "") -> str:
        expire = datetime.utcnow() + timedelta(seconds=settings.jwt_expire_seconds)
        payload = {
            "sub": str(user_id),
            "username": username,
            "role": role,
            "sid": session_token,
            "exp": expire,
        }
        return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

    def decode_token(self, token: str) -> Optional[dict]:
        try:
            return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        except JWTError:
            return None  # Fix: return None instead of {}
