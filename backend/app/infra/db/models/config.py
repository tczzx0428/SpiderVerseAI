from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.infra.db.database import Base


class SystemConfig(Base):
    __tablename__ = "system_configs"

    key = Column(String(64), primary_key=True)
    value = Column(Text, nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class ConfigHistory(Base):
    __tablename__ = "config_history"

    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(64), nullable=False, index=True)
    value = Column(Text, nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updater_name = Column(String(64), nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
