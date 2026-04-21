from __future__ import annotations
from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_container, get_current_user, get_db
from app.api.schemas.user import LoginRequest, LoginResponse, UserOut
from app.config import settings
from app.container import Container
from app.infra.db.database import SessionLocal
from app.infra.db.models.app import App
from app.infra.db.models.app_view import AppView
from app.infra.db.models.user import User
from app.core.shared.time_utils import now_cst

router = APIRouter(prefix="/api/auth", tags=["auth"])


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, response: Response,
          c: Container = Depends(get_container)):
    result = c.login.execute({"username": body.username, "password": body.password})
    token = result["access_token"]
    user = result["user"]

    response.set_cookie(
        key="sv_token", value=token,
        max_age=settings.jwt_expire_seconds, path="/",
        samesite="lax", httponly=True,  # Security fix: httpOnly=True
    )

    return LoginResponse(
        access_token=token,
        expires_in=settings.jwt_expire_seconds,
        user=UserOut.model_validate(user),
    )


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="sv_token", path="/")
    return {"message": "已退出"}


@router.get("/team-config")
def team_config(current_user: User = Depends(get_current_user),
                c: Container = Depends(get_container)):
    return c.get_team_config.execute()


@router.get("/skills")
def list_skills(c: Container = Depends(get_container),
                current_user: User = Depends(get_current_user)):
    return c.list_skills.execute()


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/change-password")
def change_password(body: ChangePasswordRequest,
                    c: Container = Depends(get_container),
                    current_user: User = Depends(get_current_user)):
    return c.change_password.execute(current_user.id, body.old_password, body.new_password)


@router.get("/verify-app")
def verify_app(request: Request, c: Container = Depends(get_container)):
    token = request.cookies.get("sv_token")
    result = c.verify_app_access.execute(token)
    if not result:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    # Record view async
    uri = request.headers.get("x-forwarded-uri", "")
    if uri:
        _record_view(uri, result["user_id"], result["username"], result["role"])

    return Response(
        status_code=200,
        headers={
            "X-SV-User": result["username"],
            "X-SV-Role": result["role"],
            "X-SV-User-Id": str(result["user_id"]),
        },
    )


def _record_view(uri: str, user_id: int, username: str, role: str):
    try:
        parts = uri.strip("/").split("/")
        if len(parts) < 2 or parts[0] != "apps":
            return
        slug = parts[1]

        db = SessionLocal()
        try:
            app = db.query(App).filter(App.slug == slug).first()
            if not app:
                return
            view = AppView(
                app_id=app.id,
                user_id=user_id if user_id else None,
                username=username, role=role,
                viewed_at=now_cst(),
            )
            db.add(view)
            db.commit()
        finally:
            db.close()
    except Exception:
        pass
