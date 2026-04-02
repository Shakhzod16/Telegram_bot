# -*- coding: utf-8 -*-
from pydantic import BaseModel, ConfigDict, Field


class CartItemAdd(BaseModel):
    product_id: int
    quantity: int = Field(ge=1, le=99)


class CartItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    quantity: int
    unit_price: int
    total_price: int
    product_name: str


class CartRead(BaseModel):
    user_id: int
    items: list[CartItemRead]
    total_amount: int
