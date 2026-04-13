from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CheckoutPreviewRequest(BaseModel):
    address_id: int = Field(..., ge=1)
    promo_code: str | None = Field(None, max_length=64)


class CheckoutPreviewResponse(BaseModel):
    subtotal: Decimal
    delivery_fee: Decimal
    discount: Decimal
    total: Decimal
    branch_name: str | None


class CreateOrderRequest(BaseModel):
    address_id: int = Field(..., ge=1)
    comment: str | None = Field(None, max_length=1024)
    promo_code: str | None = Field(None, max_length=64)
    idempotency_key: str = Field(..., min_length=8, max_length=128)


class OrderItemOut(BaseModel):
    product_id: int
    variant_id: int | None
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    snapshot_json: dict

    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    id: int
    status: str
    subtotal: Decimal
    delivery_fee: Decimal
    discount: Decimal
    total_amount: Decimal
    payment_method: str
    payment_status: str
    comment: str | None
    promo_code: str | None
    address_id: int | None
    branch_id: int | None
    created_at: datetime
    items: list[OrderItemOut] = []

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    items: list[OrderOut]
    total: int
    page: int
    size: int
