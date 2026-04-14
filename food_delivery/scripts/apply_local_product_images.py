from __future__ import annotations

import asyncio
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

from sqlalchemy import select
from sqlalchemy.orm import selectinload

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db.session import AsyncSessionLocal
from app.models.category import Category
from app.models.product import Product

IMAGES_DIR = ROOT_DIR / "app" / "webapp" / "static" / "images" / "products"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}
IMAGES_PER_CATEGORY = 4

CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "burgerlar": ("burger", "beef", "kebab", "kabob", "shawarma"),
    "salatlar": ("salad", "salat", "vegetable", "garden", "greens"),
    "ichimliklar": ("drink", "beverage", "cola", "fanta", "juice", "sharbat", "moxito", "mojito", "water"),
    "desertlar": ("dessert", "tiramisu", "cake", "cheesecake", "brownie", "napoleon", "nutella", "sweet", "🍰"),
    "setlar": ("set", "combo", "family", "office", "party", "kids", "platter", "box"),
}


def _collect_images() -> list[Path]:
    if not IMAGES_DIR.exists():
        raise FileNotFoundError(f"Images directory not found: {IMAGES_DIR}")
    files = [p for p in IMAGES_DIR.iterdir() if p.is_file() and p.suffix.lower() in ALLOWED_EXTENSIONS]
    files.sort(key=lambda p: p.name.lower())
    if not files:
        raise RuntimeError(f"No image files found in: {IMAGES_DIR}")
    return files


def _build_public_url(file_name: str) -> str:
    return f"/static/images/products/{quote(file_name)}"


def _category_key(category: Category) -> str:
    raw = (category.name_uz or "").strip().lower()
    return raw


def _build_category_image_map(categories: list[Category], images: list[Path]) -> dict[int, list[Path]]:
    used: set[Path] = set()
    unknown = list(images)
    mapping: dict[int, list[Path]] = {}

    for category in categories:
        key = _category_key(category)
        keywords = CATEGORY_KEYWORDS.get(key, ())
        matched: list[Path] = []

        if keywords:
            for image in images:
                if image in used:
                    continue
                lname = image.name.lower()
                if any(token in lname for token in keywords):
                    matched.append(image)
                    used.add(image)
                    if len(matched) == IMAGES_PER_CATEGORY:
                        break

        mapping[category.id] = matched

    unknown = [img for img in unknown if img not in used]

    # Fill remaining slots from unassigned images first.
    for category in categories:
        selected = mapping[category.id]
        while len(selected) < IMAGES_PER_CATEGORY and unknown:
            selected.append(unknown.pop(0))

    # If still missing, reuse from whole image set cyclically.
    if images:
        for category in categories:
            selected = mapping[category.id]
            if len(selected) < IMAGES_PER_CATEGORY:
                idx = 0
                while len(selected) < IMAGES_PER_CATEGORY:
                    selected.append(images[idx % len(images)])
                    idx += 1

    return mapping


async def main() -> None:
    images = _collect_images()
    print(f"Found {len(images)} local images in {IMAGES_DIR}")

    async with AsyncSessionLocal() as session:
        category_result = await session.execute(select(Category).order_by(Category.id))
        categories = list(category_result.scalars().all())
        if not categories:
            print("No categories found. Nothing to update.")
            return

        product_result = await session.execute(
            select(Product).options(selectinload(Product.category)).order_by(Product.category_id, Product.id)
        )
        products = list(product_result.scalars().all())
        if not products:
            print("No products found. Nothing to update.")
            return

        cat_images = _build_category_image_map(categories, images)
        products_by_category: dict[int, list[Product]] = defaultdict(list)
        for product in products:
            products_by_category[product.category_id].append(product)

        updated = 0
        for category in categories:
            cat_id = category.id
            assigned_images = cat_images.get(cat_id) or images[:IMAGES_PER_CATEGORY]
            cat_products = products_by_category.get(cat_id, [])
            if not cat_products:
                continue

            for idx, product in enumerate(cat_products):
                chosen = assigned_images[idx % len(assigned_images)]
                image_url = _build_public_url(chosen.name)
                if product.image_url != image_url:
                    product.image_url = image_url
                    updated += 1

            print(
                f"[{category.id}] {category.name_uz}: "
                + ", ".join(_build_public_url(path.name) for path in assigned_images)
            )

        await session.commit()
        print(f"Updated product images: {updated}/{len(products)}")


if __name__ == "__main__":
    asyncio.run(main())
