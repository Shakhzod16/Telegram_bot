from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.address import Address
    from app.models.cart import Cart
    from app.models.order import Order


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger(), nullable=False, unique=True, index=True)
    group_chat_id: Mapped[int | None] = mapped_column(BigInteger(), nullable=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    language: Mapped[str] = mapped_column(String(5), nullable=False, default="uz")
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    is_superadmin: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    owner_id: Mapped[int | None] = mapped_column(Integer(), ForeignKey("users.id"), nullable=True)

    # Relationships
    addresses: Mapped[list["Address"]] = relationship(back_populates="user", lazy="selectin")
    orders: Mapped[list["Order"]] = relationship(back_populates="user", lazy="selectin")
    cart: Mapped["Cart | None"] = relationship(back_populates="user", uselist=False, lazy="selectin")

    @property
    def full_name(self) -> str:
        parts = [part.strip() for part in ((self.first_name or ""), (self.last_name or "")) if part and part.strip()]
        if parts:
            return " ".join(parts)
        if self.username:
            return f"@{self.username}"
        return "Foydalanuvchi"
