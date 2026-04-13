from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.category import Category


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False, index=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    name_uz: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ru: Mapped[str] = mapped_column(String(255), nullable=False)
    description_uz: Mapped[str | None] = mapped_column(Text(), nullable=True)
    description_ru: Mapped[str | None] = mapped_column(Text(), nullable=True)
    base_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    weight_grams: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean(), default=True, index=True)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    category: Mapped["Category"] = relationship(back_populates="products")
    variants: Mapped[list["ProductVariant"]] = relationship(
        back_populates="product",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    modifiers: Mapped[list["ProductModifier"]] = relationship(
        back_populates="product",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class ProductVariant(Base):
    __tablename__ = "product_variants"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    name_uz: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ru: Mapped[str] = mapped_column(String(255), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    weight_grams: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean(), default=False)

    product: Mapped["Product"] = relationship(back_populates="variants")


class ProductModifier(Base):
    __tablename__ = "product_modifiers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    name_uz: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ru: Mapped[str] = mapped_column(String(255), nullable=False)
    price_delta: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    is_required: Mapped[bool] = mapped_column(Boolean(), default=False)

    product: Mapped["Product"] = relationship(back_populates="modifiers")
