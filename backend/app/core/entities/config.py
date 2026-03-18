from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ConfigEntity:
    key: str
    value: str
    updated_by: Optional[int] = None
    updated_at: Optional[datetime] = None


@dataclass
class ConfigHistoryEntity:
    id: int
    config_key: str
    value: str
    updated_by: Optional[int] = None
    updater_name: Optional[str] = None
    updated_at: Optional[datetime] = None
