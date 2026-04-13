from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CategoryOut(BaseModel):
    id: int
    name_uz: str
    name_ru: str
    image_url: str | None
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class ProductVariantOut(BaseModel):
    id: int
    name_uz: str
    name_ru: str
    price: Decimal
    weight_grams: int | None
    is_default: bool

    model_config = ConfigDict(from_attributes=True)


class ProductModifierOut(BaseModel):
    id: int
    name_uz: str
    name_ru: str
    price_delta: Decimal
    is_required: bool

    model_config = ConfigDict(from_attributes=True)


class ProductListOut(BaseModel):
    id: int
    name_uz: str
    name_ru: str
    base_price: Decimal
    weight_grams: int | None
    image_url: str | None
    category_id: int

    model_config = ConfigDict(from_attributes=True)


class ProductDetailOut(ProductListOut):
    description_uz: str | None
    description_ru: str | None
    variants: list[ProductVariantOut]
    modifiers: list[ProductModifierOut]


class PaginatedProducts(BaseModel):
    items: list[ProductListOut]
    total: int
    page: int
    size: int


# Backward-compatible aliases used by current services/imports.
ProductShort = ProductListOut
ProductDetail = ProductDetailOut
