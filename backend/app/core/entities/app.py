from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class AppEntity:
    id: int
    name: str
    slug: str
    owner_id: int
    status: str = "pending"
    description: Optional[str] = None
    container_id: Optional[str] = None
    container_name: Optional[str] = None
    host_port: Optional[int] = None
    upload_path: Optional[str] = None
    build_log: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
