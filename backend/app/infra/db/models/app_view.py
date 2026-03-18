from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from app.infra.db.database import Base
from app.core.shared.time_utils import now_cst


class AppView(Base):
    __tablename__ = "app_views"

    id = Column(Integer, primary_key=True)
    app_id = Column(Integer, ForeignKey("apps.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    username = Column(String(64), nullable=False)
    role = Column(String(16), nullable=False, default="user")
    viewed_at = Column(DateTime, nullable=False, default=now_cst)
