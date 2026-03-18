from __future__ import annotations
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PromptCreate(BaseModel):
    title: str
    content: str
    category: Optional[str] = None
    sort_order: int = 0


class PromptUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class PromptOut(BaseModel):
    id: int
    title: str
    content: str
    category: Optional[str]
    sort_order: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
