from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.user import User


class Address(Base):
    __tablename__ = "addresses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address_line: Mapped[str] = mapped_column(String(500), nullable=False)
    lat: Mapped[float | None] = mapped_column(Float(), nullable=True)
    lng: Mapped[float | None] = mapped_column(Float(), nullable=True)
    apartment: Mapped[str | None] = mapped_column(String(20), nullable=True)
    floor: Mapped[str | None] = mapped_column(String(10), nullable=True)
    entrance: Mapped[str | None] = mapped_column(String(10), nullable=True)
    door_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    landmark: Mapped[str | None] = mapped_column(String(300), nullable=True)
    comment: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="addresses")
    orders: Mapped[list["Order"]] = relationship(back_populates="address")
