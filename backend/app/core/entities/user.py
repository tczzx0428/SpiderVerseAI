from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class UserEntity:
    id: int
    username: str
    hashed_pw: str
    role: str = "user"
    email: Optional[str] = None
    is_active: bool = True
    session_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
