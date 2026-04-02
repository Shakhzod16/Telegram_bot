# -*- coding: utf-8 -*-
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from backend.schemas.address import AddressCreate, AddressRead
from backend.schemas.cart import CartItemAdd, CartItemRead


class OrderCreate(BaseModel):
    user_id: int
    items: list[CartItemAdd]
    location: AddressCreate | None = None
    payment_method: str = "click"


class OrderRead(BaseModel):
    order_id: int
    status: str
    total_amount: int
    payment_method: str


class OrderStatusUpdate(BaseModel):
    status: str


class OrderActionRead(BaseModel):
    ok: bool
    order_id: int
    status: str


class OrderUserSummary(BaseModel):
    telegram_user_id: int | None = None
    name: str = ""
    phone: str = ""


class OrderItemAdminRead(BaseModel):
    name: str
    quantity: int
    unit_price: int
    total_price: int


class OrderAdminRead(BaseModel):
    id: int
    status: str
    total_amount: int
    payment_method: str
    payment_status: str | None = None
    created_at: datetime | None = None
    paid_at: datetime | None = None
    delivered_at: datetime | None = None
    user: OrderUserSummary
    items: list[OrderItemAdminRead]


class OrderDetailsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    status: str
    total_amount: int
    location_label: str
    latitude: float | None = None
    longitude: float | None = None
    created_at: datetime | None = None
    items: list[CartItemRead]
    location: AddressRead | None = None
