# -*- coding: utf-8 -*-
import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db import Base


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentMethod(str, enum.Enum):
    CLICK = "click"
    PAYME = "payme"
    CASH = "cash"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(128), default="")
    last_name: Mapped[str] = mapped_column(String(128), default="")
    username: Mapped[str] = mapped_column(String(128), default="")
    phone: Mapped[str] = mapped_column(String(40), default="")
    language: Mapped[str] = mapped_column(String(8), default="en", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    addresses: Mapped[list["Address"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        order_by=lambda: (Address.is_default.desc(), Address.id),
    )


class Address(Base):
    __tablename__ = "addresses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    label: Mapped[str] = mapped_column(String(80), default="")
    address_text: Mapped[str] = mapped_column(Text, default="")
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="addresses")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(String(40), index=True)
    name_uz: Mapped[str] = mapped_column(String(255))
    name_ru: Mapped[str] = mapped_column(String(255))
    name_en: Mapped[str] = mapped_column(String(255))
    description_uz: Mapped[str] = mapped_column(Text, default="")
    description_ru: Mapped[str] = mapped_column(Text, default="")
    description_en: Mapped[str] = mapped_column(Text, default="")
    price: Mapped[int] = mapped_column(Integer)
    image_url: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default=OrderStatus.PENDING.value, index=True)
    payment_method: Mapped[str] = mapped_column(String(20), default=PaymentMethod.CASH.value, index=True)
    total_amount: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(8), default="UZS")
    location_label: Mapped[str] = mapped_column(Text, default="")
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    pending_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship()
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    payments: Mapped[list["Payment"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    status_history: Mapped[list["OrderStatusHistory"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderStatusHistory.changed_at",
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[int] = mapped_column(Integer)
    total_price: Mapped[int] = mapped_column(Integer)
    product_name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    order: Mapped["Order"] = relationship(back_populates="items")


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    old_status: Mapped[str] = mapped_column(String(32), default="")
    new_status: Mapped[str] = mapped_column(String(32))
    changed_by: Mapped[str] = mapped_column(String(128), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    order: Mapped["Order"] = relationship(back_populates="status_history")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    provider: Mapped[str] = mapped_column(String(20), index=True)
    amount: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    payment_url: Mapped[str] = mapped_column(Text, default="")
    external_id: Mapped[str] = mapped_column(String(255), default="", index=True)
    raw_payload: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    order: Mapped["Order"] = relationship(back_populates="payments")
