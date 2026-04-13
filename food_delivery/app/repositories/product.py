from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.exceptions import ValidationAppError
from app.models.category import Category
from app.models.product import Product, ProductModifier, ProductVariant
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    model = Category

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_active_all(self) -> list[Category]:
        stmt = select(Category).where(Category.is_active.is_(True)).order_by(Category.sort_order, Category.id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # Backward-compatible method used by existing services.
    async def list_active(self) -> list[Category]:
        return await self.get_active_all()

    # Backward-compatible method used by existing admin endpoints.
    async def list_all_admin(self) -> list[Category]:
        stmt = select(Category).order_by(Category.sort_order, Category.id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class ProductRepository(BaseRepository[Product]):
    model = Product

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_paginated(
        self,
        page: int = 1,
        size: int = 20,
        category_id: int | None = None,
        search: str | None = None,
    ) -> tuple[list[Product], int]:
        page = max(1, int(page))
        size = min(max(1, int(size)), 100)

        filters = [Product.is_active.is_(True)]
        if category_id is not None:
            filters.append(Product.category_id == category_id)
        if search and search.strip():
            q = f"%{search.strip()}%"
            filters.append(or_(Product.name_uz.ilike(q), Product.name_ru.ilike(q)))

        count_stmt = select(func.count(Product.id)).where(*filters)
        total_raw = await self.execute_scalar(count_stmt)
        total = int(total_raw or 0)

        stmt = (
            select(Product)
            .where(*filters)
            .order_by(Product.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def get_with_details(self, product_id: int) -> Product | None:
        stmt = (
            select(Product)
            .options(
                joinedload(Product.variants),
                joinedload(Product.modifiers),
                joinedload(Product.category),
            )
            .where(Product.id == product_id)
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def verify_prices(self, items: list[dict]) -> list[dict]:
        if not items:
            return []

        product_ids: set[int] = set()
        for item in items:
            try:
                product_ids.add(int(item.get("product_id")))
            except (TypeError, ValueError) as exc:
                raise ValidationAppError("Invalid product_id") from exc

        stmt = (
            select(Product)
            .options(selectinload(Product.variants), selectinload(Product.modifiers))
            .where(Product.id.in_(product_ids), Product.is_active.is_(True))
        )
        result = await self.session.execute(stmt)
        products = list(result.scalars().all())
        product_map = {product.id: product for product in products}

        verified: list[dict[str, Any]] = []
        for item in items:
            try:
                product_id = int(item.get("product_id"))
                quantity = int(item.get("quantity", 1))
            except (TypeError, ValueError) as exc:
                raise ValidationAppError("Invalid checkout line data") from exc

            if quantity <= 0:
                raise ValidationAppError("Quantity must be greater than zero")

            product = product_map.get(product_id)
            if product is None:
                raise ValidationAppError(f"Product unavailable: {product_id}")

            variant_id_input = item.get("variant_id")
            variant_id: int | None = None
            unit_price = product.base_price
            variant_name: str | None = None

            if product.variants:
                if variant_id_input is None:
                    variant = next((row for row in product.variants if row.is_default), product.variants[0])
                else:
                    try:
                        variant_id_value = int(variant_id_input)
                    except (TypeError, ValueError) as exc:
                        raise ValidationAppError("Invalid variant") from exc
                    variant = next((row for row in product.variants if row.id == variant_id_value), None)
                    if variant is None:
                        raise ValidationAppError("Invalid variant")
                variant_id = variant.id
                variant_name = variant.name_uz
                unit_price = variant.price
            elif variant_id_input is not None:
                raise ValidationAppError("Variant is not supported for this product")

            modifier_ids_raw = item.get("modifier_ids") or []
            if not isinstance(modifier_ids_raw, list):
                raise ValidationAppError("modifier_ids must be a list")

            modifier_map = {modifier.id: modifier for modifier in product.modifiers}
            normalized_modifier_ids: list[int] = []
            modifiers_snapshot: list[dict[str, Any]] = []
            extra = Decimal("0")
            for modifier_id_raw in modifier_ids_raw:
                try:
                    modifier_id = int(modifier_id_raw)
                except (TypeError, ValueError) as exc:
                    raise ValidationAppError("Invalid modifier") from exc
                modifier = modifier_map.get(modifier_id)
                if modifier is None:
                    raise ValidationAppError("Invalid modifier")
                normalized_modifier_ids.append(modifier_id)
                extra += modifier.price_delta
                modifiers_snapshot.append(
                    {
                        "id": modifier.id,
                        "name_uz": modifier.name_uz,
                        "price_delta": str(modifier.price_delta),
                    }
                )

            required_modifier_ids = {modifier.id for modifier in product.modifiers if modifier.is_required}
            if not required_modifier_ids.issubset(set(normalized_modifier_ids)):
                raise ValidationAppError("Missing required modifiers")

            unit_price = unit_price + extra
            total_price = unit_price * quantity

            verified.append(
                {
                    "product_id": product.id,
                    "variant_id": variant_id,
                    "quantity": quantity,
                    "modifier_ids": normalized_modifier_ids,
                    "unit_price": unit_price,
                    "total_price": total_price,
                    "snapshot": {
                        "product_name": product.name_uz,
                        "variant_name": variant_name,
                        "variant_id": variant_id,
                        "image_url": product.image_url,
                        "modifier_ids": normalized_modifier_ids,
                        "modifiers": modifiers_snapshot,
                    },
                }
            )
        return verified

    # Backward-compatible method used by existing services.
    async def list_paginated(
        self,
        *,
        category_id: int | None,
        search: str | None,
        page: int,
        size: int,
    ) -> tuple[list[Product], int]:
        return await self.get_paginated(page=page, size=size, category_id=category_id, search=search)

    # Backward-compatible method used by existing services.
    async def get_by_id_with_relations(self, product_id: int) -> Product | None:
        return await self.get_with_details(product_id)

    async def get_variant(self, variant_id: int) -> ProductVariant | None:
        return await self.session.get(ProductVariant, variant_id)

    async def get_modifiers_for_product(self, product_id: int) -> list[ProductModifier]:
        stmt = select(ProductModifier).where(ProductModifier.product_id == product_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
