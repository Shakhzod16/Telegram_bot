from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AdminPhoneWhitelist(Base):
    __tablename__ = "admin_phone_whitelist"

    id: Mapped[int] = mapped_column(Integer(), primary_key=True, autoincrement=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    added_by: Mapped[int | None] = mapped_column(Integer(), ForeignKey("users.id"), nullable=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean(), default=True, nullable=False)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
