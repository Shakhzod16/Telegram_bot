# -*- coding: utf-8 -*-
from pydantic import BaseModel


class ReorderItemRead(BaseModel):
    product_id: int
    quantity: int
    name: str


class ReorderRead(BaseModel):
    order_id: int
    items: list[ReorderItemRead]
    skipped_count: int = 0
    skipped_products: list[str] = []
