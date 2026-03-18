from __future__ import annotations
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    role: str = "user"
    is_active: bool = True


class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    role: str = "user"
    expires_at: Optional[datetime] = None


class BatchUserCreate(BaseModel):
    project_name: str          # 项目名称，用于生成用户名前缀
    start_index: int = 1       # 起始序号
    count: int                 # 生成数量
    password: str              # 统一密码
    expires_at: Optional[datetime] = None  # 可选过期时间


class UserUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None
    email: Optional[str] = None
    expires_at: Optional[datetime] = None


class UserOut(UserBase):
    id: int
    expires_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut
