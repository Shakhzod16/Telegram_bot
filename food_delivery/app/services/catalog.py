from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.product import Product
from app.repositories.category import CategoryRepository
from app.repositories.product import ProductRepository
from app.schemas.catalog import (
    CategoryOut,
    PaginatedProducts,
    ProductDetailOut,
    ProductListOut,
    ProductModifierOut,
    ProductVariantOut,
)


class CatalogService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._categories = CategoryRepository(session)
        self._products = ProductRepository(session)

    async def list_categories(self) -> list[CategoryOut]:
        rows = await self._categories.list_active()
        return [CategoryOut.model_validate(c) for c in rows]

    async def list_products(
        self,
        *,
        category_id: int | None,
        search: str | None,
        page: int,
        size: int,
    ) -> PaginatedProducts:
        items, total = await self._products.list_paginated(
            category_id=category_id,
            search=search,
            page=page,
            size=size,
        )
        return PaginatedProducts(
            items=[ProductListOut.model_validate(p) for p in items],
            total=total,
            page=page,
            size=size,
        )

    async def get_product(self, product_id: int) -> ProductDetailOut:
        p = await self._products.get_by_id_with_relations(product_id)
        if not p or not p.is_active:
            raise NotFoundError("Product not found")
        return ProductDetailOut(
            id=p.id,
            category_id=p.category_id,
            name_uz=p.name_uz,
            name_ru=p.name_ru,
            description_uz=p.description_uz,
            description_ru=p.description_ru,
            base_price=p.base_price,
            weight_grams=p.weight_grams,
            image_url=p.image_url,
            variants=[ProductVariantOut.model_validate(v) for v in p.variants],
            modifiers=[ProductModifierOut.model_validate(m) for m in p.modifiers],
        )

    async def get_product_model(self, product_id: int) -> Product:
        p = await self._products.get_by_id_with_relations(product_id)
        if not p:
            raise NotFoundError("Product not found")
        return p
