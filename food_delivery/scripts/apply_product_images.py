from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from urllib.parse import quote

from sqlalchemy import select
from sqlalchemy.orm import selectinload

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db.session import AsyncSessionLocal
from app.models.product import Product


def _pick_query(name: str, category_name: str) -> str:
    n = (name or "").lower()
    c = (category_name or "").lower()

    if "burger" in n or "burger" in c:
        return "burger,fast food,meal"
    if any(word in n for word in ("salat", "sezar", "grek", "tuna", "vitamin")) or "salat" in c:
        return "salad,fresh food,bowl"
    if any(word in n for word in ("cola", "fanta", "sharbat", "moxito", "ichimlik")) or "ichimlik" in c:
        return "soft drink,beverage,cold drink"
    if any(word in n for word in ("cheesecake", "brownie", "napoleon", "tiramisu", "desert")) or "desert" in c:
        return "dessert,cake,sweet"
    if "set" in n or "setlar" in c:
        return "food platter,combo meal,party food"
    return "food,dish,restaurant"


def _build_image_url(product_id: int, query: str) -> str:
    encoded_query = quote(query, safe=",")
    return f"https://source.unsplash.com/1200x900/?{encoded_query}&sig={product_id}"


async def main() -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Product).options(selectinload(Product.category)).order_by(Product.id)
        )
        products = list(result.scalars().all())
        updated = 0

        for product in products:
            category_name = product.category.name_uz if product.category else ""
            query = _pick_query(product.name_uz, category_name)
            image_url = _build_image_url(product.id, query)
            if product.image_url != image_url:
                product.image_url = image_url
                updated += 1

        await session.commit()
        print(f"Updated product images: {updated}/{len(products)}")


if __name__ == "__main__":
    asyncio.run(main())
