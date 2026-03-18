from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class PromptEntity:
    id: int
    title: str
    content: str
    category: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
