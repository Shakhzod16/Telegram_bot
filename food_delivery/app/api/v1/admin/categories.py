from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.user import User
from app.repositories.category import CategoryRepository
from app.schemas.admin import CategoryCreateAdmin, CategoryUpdateAdmin
from app.services.admin import AdminService

router = APIRouter()


@router.get("")
async def list_categories(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> list:
    return await CategoryRepository(db).list_all_admin()


@router.post("")
async def create_category(
    body: CategoryCreateAdmin,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return await AdminService(db).create_category(body)


@router.put("/{category_id}")
async def update_category(
    category_id: int,
    body: CategoryUpdateAdmin,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return await AdminService(db).update_category(category_id, body)


@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict:
    await AdminService(db).delete_category(category_id)
    return {"success": True}
