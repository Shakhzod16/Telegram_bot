# -*- coding: utf-8 -*-
from pydantic import BaseModel, ConfigDict


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    name: str
    description: str
    price: int
    image_url: str


class CategoryRead(BaseModel):
    category: str
    products: list[ProductRead]
