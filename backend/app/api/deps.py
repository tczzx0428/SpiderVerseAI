from __future__ import annotations
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.container import Container, build_container
from app.infra.auth.jwt_auth import JwtAuthProvider
from app.infra.db.database import SessionLocal
from app.infra.db.models.user import User

bearer_scheme = HTTPBearer()
_auth_provider = JwtAuthProvider()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_container(db: Session = Depends(get_db)) -> Container:
    return build_container(db)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    payload = _auth_provider.decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 Token",
        )

    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已禁用",
        )

    # 登录互踢
    jwt_sid = payload.get("sid", "")
    if user.session_token and jwt_sid != user.session_token:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="您的账号已在其他地方登录",
        )

    # 过期检查
    if user.expires_at is not None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if user.expires_at < now:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账号已过期，请联系管理员",
            )

    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return current_user
