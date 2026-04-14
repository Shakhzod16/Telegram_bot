from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import check_resource_ownership, get_owner_filter, require_admin
from app.db.session import get_db
from app.models.product import Product
from app.models.user import User
from app.schemas.admin import ProductCreateAdmin, ProductUpdateAdmin

router = APIRouter()


def _product_to_dict(product: Product) -> dict:
    return {
        "id": product.id,
        "category_id": product.category_id,
        "owner_id": product.owner_id,
        "name_uz": product.name_uz,
        "name_ru": product.name_ru,
        "description_uz": product.description_uz,
        "description_ru": product.description_ru,
        "base_price": str(product.base_price),
        "weight_grams": product.weight_grams,
        "image_url": product.image_url,
        "is_active": product.is_active,
    }


async def get_product_or_404(product_id: int, db: AsyncSession) -> Product:
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return product


@router.get("")
async def list_products(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> list[dict]:
    owner_filter = get_owner_filter(current_user)
    query = select(Product)
    if owner_filter is not None:
        query = query.where(Product.owner_id == owner_filter)

    query = query.order_by(Product.id.desc()).limit(500)
    res = await db.execute(query)
    rows = list(res.scalars().all())
    return [_product_to_dict(p) for p in rows]


@router.post("")
async def create_product(
    body: ProductCreateAdmin,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    product_data = body.model_dump()
    requested_owner_id = product_data.pop("owner_id", None)
    owner_id = current_user.id
    if current_user.is_superadmin and requested_owner_id is not None:
        owner_id = requested_owner_id

    new_product = Product(**product_data, owner_id=owner_id)
    db.add(new_product)
    await db.flush()
    await db.refresh(new_product)
    return _product_to_dict(new_product)


@router.get("/{product_id}")
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    product = await get_product_or_404(product_id, db)
    check_resource_ownership(product.owner_id, current_user)
    return _product_to_dict(product)


@router.put("/{product_id}")
async def update_product(
    product_id: int,
    body: ProductUpdateAdmin,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    product = await get_product_or_404(product_id, db)
    check_resource_ownership(product.owner_id, current_user)

    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(product, key, value)
    await db.flush()
    await db.refresh(product)
    return _product_to_dict(product)


@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    product = await get_product_or_404(product_id, db)
    check_resource_ownership(product.owner_id, current_user)
    db.delete(product)
    await db.flush()
    return {"success": True}
