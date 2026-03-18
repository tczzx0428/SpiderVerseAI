from __future__ import annotations
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.errors import (
    AccountDisabled,
    AccountExpired,
    AppBuildInProgress,
    AppNotFound,
    CannotDeleteSelf,
    Forbidden,
    InvalidFile,
    InvalidPassword,
    NoContainer,
    NoUploadedCode,
    PromptNotFound,
    SessionConflict,
    SkillNotFound,
    SlugTaken,
    Unauthorized,
    UserNotFound,
    UsernameExists,
)

_STATUS_MAP = {
    AppNotFound: 404,
    UserNotFound: 404,
    PromptNotFound: 404,
    SkillNotFound: 404,
    SlugTaken: 400,
    UsernameExists: 400,
    InvalidFile: 400,
    InvalidPassword: 400,
    AppBuildInProgress: 400,
    NoUploadedCode: 400,
    NoContainer: 400,
    CannotDeleteSelf: 400,
    Unauthorized: 401,
    AccountDisabled: 403,
    Forbidden: 403,
    AccountExpired: 403,
    SessionConflict: 409,
}


def setup_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def business_error_handler(request: Request, exc: Exception):
        status_code = _STATUS_MAP.get(type(exc))
        if status_code is not None:
            return JSONResponse(
                status_code=status_code,
                content={"detail": str(exc)},
            )
        # Let other exceptions propagate to FastAPI's default handler
        raise exc
