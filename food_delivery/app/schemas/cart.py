from decimal import Decimal

from pydantic import BaseModel, Field


class CartItemModifier(BaseModel):
    id: int
    name_uz: str
    price_delta: Decimal


class CartLineOut(BaseModel):
    id: str
    line_key: str
    product_id: int
    product_name: str
    variant_id: int | None
    variant_name: str | None
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    modifiers: list[CartItemModifier] = []
    snapshot: dict = {}
    unavailable: bool = False


class CartOut(BaseModel):
    items: list[CartLineOut]
    subtotal: Decimal
    currency: str = "UZS"


class CartAddItem(BaseModel):
    product_id: int = Field(..., ge=1)
    variant_id: int | None = None
    quantity: int = Field(1, ge=1, le=99)
    modifier_ids: list[int] = Field(default_factory=list)


class CartPatchItem(BaseModel):
    quantity: int = Field(..., ge=0, le=99)
