from datetime import datetime, time
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class ProductCreateAdmin(BaseModel):
    category_id: int
    owner_id: int | None = None
    name_uz: str
    name_ru: str
    description_uz: str | None = None
    description_ru: str | None = None
    base_price: Decimal
    weight_grams: int | None = None
    image_url: str | None = None
    is_active: bool = True


class ProductUpdateAdmin(BaseModel):
    category_id: int | None = None
    name_uz: str | None = None
    name_ru: str | None = None
    description_uz: str | None = None
    description_ru: str | None = None
    base_price: Decimal | None = None
    weight_grams: int | None = None
    image_url: str | None = None
    is_active: bool | None = None


class ProductUpdate(BaseModel):
    name_uz: Optional[str] = None
    name_ru: Optional[str] = None
    base_price: Optional[float] = None
    description: Optional[str] = None
    weight_grams: Optional[int] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None
    category_id: Optional[int] = None
    sort_order: Optional[int] = None


class CategoryCreateAdmin(BaseModel):
    name_uz: str
    name_ru: str
    image_url: str | None = None
    sort_order: int = 0
    is_active: bool = True


class CategoryUpdateAdmin(BaseModel):
    name_uz: str | None = None
    name_ru: str | None = None
    image_url: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class BranchCreateAdmin(BaseModel):
    name: str
    lat: float
    lng: float
    radius_km: float = 5.0
    address: str
    phone: str | None = None
    is_active: bool = True
    open_time: time
    close_time: time
    delivery_fee: float = 0.0


class BranchUpdateAdmin(BaseModel):
    name: str | None = None
    lat: float | None = None
    lng: float | None = None
    radius_km: float | None = None
    address: str | None = None
    phone: str | None = None
    is_active: bool | None = None
    open_time: time | None = None
    close_time: time | None = None
    delivery_fee: float | None = None


class PromoCreateAdmin(BaseModel):
    code: str = Field(..., min_length=2, max_length=64)
    discount_type: str = Field(..., pattern="^(percent|fixed)$")
    discount_value: Decimal
    min_order_amount: Decimal = Decimal("0")
    max_uses: int | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    is_active: bool = True


class PromoUpdateAdmin(BaseModel):
    discount_type: str | None = Field(None, pattern="^(percent|fixed)$")
    discount_value: Decimal | None = None
    min_order_amount: Decimal | None = None
    max_uses: int | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    is_active: bool | None = None


class OrderStatusPatch(BaseModel):
    status: str = Field(
        ...,
        pattern="^(pending|in_progress|delivered|cancelled)$",
    )
