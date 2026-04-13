from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.user import User
from app.repositories.promo import PromoRepository
from app.schemas.admin import PromoCreateAdmin, PromoUpdateAdmin
from app.services.admin import AdminService

router = APIRouter()


@router.get("")
async def list_promos(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> list:
    return await PromoRepository(db).list_all()


@router.post("")
async def create_promo(
    body: PromoCreateAdmin,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return await AdminService(db).create_promo(body)


@router.put("/{promo_id}")
async def update_promo(
    promo_id: int,
    body: PromoUpdateAdmin,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return await AdminService(db).update_promo(promo_id, body)


@router.delete("/{promo_id}")
async def delete_promo(
    promo_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict:
    await AdminService(db).delete_promo(promo_id)
    return {"success": True}
