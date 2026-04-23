from __future__ import annotations
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Boolean

from app.infra.db.database import Base
from app.core.shared.time_utils import now_cst


class AIModelConfig(Base):
    __tablename__ = "ai_model_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), nullable=False)
    provider = Column(String(32), nullable=False)
    model_id = Column(String(128), nullable=False)

    api_key = Column(String(512), nullable=False)
    base_url = Column(String(512), nullable=False)

    usage = Column(String(16), nullable=False, default="chat")

    is_enabled = Column(Boolean, nullable=False, default=True)

    priority = Column(Integer, nullable=False, default=0)

    description = Column(Text, nullable=True)

    system_prompt = Column(Text, nullable=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime, nullable=False, default=now_cst, onupdate=now_cst)
    created_at = Column(DateTime, nullable=False, default=now_cst)