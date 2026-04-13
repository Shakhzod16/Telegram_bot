from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.admin import ProductCreateAdmin, ProductUpdateAdmin
from app.services.admin import AdminService

router = APIRouter()


@router.get("")
async def list_products(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> list[dict]:
    from sqlalchemy import select

    from app.models.product import Product

    res = await db.execute(select(Product).order_by(Product.id.desc()).limit(500))
    rows = list(res.scalars().all())
    return [
        {
            "id": p.id,
            "category_id": p.category_id,
            "name_uz": p.name_uz,
            "name_ru": p.name_ru,
            "base_price": str(p.base_price),
            "is_active": p.is_active,
        }
        for p in rows
    ]


@router.post("")
async def create_product(
    body: ProductCreateAdmin,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return await AdminService(db).create_product(body)


@router.put("/{product_id}")
async def update_product(
    product_id: int,
    body: ProductUpdateAdmin,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return await AdminService(db).update_product(product_id, body)


@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict:
    await AdminService(db).delete_product(product_id)
    return {"success": True}
