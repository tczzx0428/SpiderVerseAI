from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class SkillEntity:
    name: str
    content: str
    description: str = ""
    category: str = "other"
    author_id: Optional[int] = None
    author_name: str = ""
    installs: int = 0
    pinned: bool = False
    version: str = "1.0.0"
    changelog: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
