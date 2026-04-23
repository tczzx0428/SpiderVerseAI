from __future__ import annotations
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, JSON

from app.infra.db.database import Base
from app.core.shared.time_utils import now_cst


class AICreation(Base):
    __tablename__ = "ai_creations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(256), nullable=True)

    # 对话历史: [{"role": "user/assistant", "content": "..."}]
    conversation = Column(JSON, nullable=True, default=list)

    # 状态: chatting | generating | building | running | failed | cancelled
    status = Column(String(32), nullable=False, default="chatting")

    # 生成的代码
    generated_code = Column(JSON, nullable=True)  # {"app.py": "...", "requirements.txt": "..."}

    # 关联的应用ID (创建完成后)
    app_id = Column(Integer, nullable=True)

    # 进度信息
    progress = Column(Integer, nullable=False, default=0)  # 0-100
    progress_message = Column(String(512), nullable=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=now_cst)
    updated_at = Column(DateTime, nullable=False, default=now_cst, onupdate=now_cst)