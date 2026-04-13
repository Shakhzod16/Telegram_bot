from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from urllib.parse import quote

from sqlalchemy import select

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db.session import AsyncSessionLocal
from app.models.product import Product

IMAGES_DIR = ROOT_DIR / "app" / "webapp" / "static" / "images" / "products"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}


def _collect_images() -> list[Path]:
    if not IMAGES_DIR.exists():
        raise FileNotFoundError(f"Images directory not found: {IMAGES_DIR}")
    files = [p for p in IMAGES_DIR.iterdir() if p.is_file() and p.suffix.lower() in ALLOWED_EXTENSIONS]
    files.sort(key=lambda p: p.name.lower())
    if not files:
        raise RuntimeError(f"No image files found in: {IMAGES_DIR}")
    return files


def _build_public_url(file_name: str) -> str:
    # Keep URL safe even when file names contain spaces, brackets, or Unicode.
    return f"/static/images/products/{quote(file_name)}"


async def main() -> None:
    images = _collect_images()
    print(f"Found {len(images)} local images in {IMAGES_DIR}")

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Product).order_by(Product.id))
        products = list(result.scalars().all())
        if not products:
            print("No products found. Nothing to update.")
            return

        updated = 0
        for idx, product in enumerate(products):
            image_file = images[idx % len(images)]
            image_url = _build_public_url(image_file.name)
            if product.image_url != image_url:
                product.image_url = image_url
                updated += 1

        await session.commit()

    print(f"Updated product images: {updated}/{len(products)}")
    for idx, image in enumerate(images, start=1):
        label = image.name.encode("cp1251", errors="replace").decode("cp1251")
        print(f"{idx}. {label} -> {_build_public_url(image.name)}")


if __name__ == "__main__":
    asyncio.run(main())
