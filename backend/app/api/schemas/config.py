from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ConfigOut(BaseModel):
    key: str
    value: str
    updated_by: Optional[int] = None
    updater_name: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class ConfigUpdate(BaseModel):
    value: str


class ConfigHistoryOut(BaseModel):
    id: int
    config_key: str
    value: str
    updater_name: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True
