# -*- coding: utf-8 -*-
from pydantic import BaseModel

from backend.schemas.address import AddressRead
from backend.schemas.product import ProductRead


class BootstrapUser(BaseModel):
    id: int
    user_id: int
    first_name: str
    language: str


class BootstrapResponse(BaseModel):
    user: BootstrapUser
    products: list[ProductRead]
    texts: dict[str, str]
    saved_addresses: list[AddressRead] = []
