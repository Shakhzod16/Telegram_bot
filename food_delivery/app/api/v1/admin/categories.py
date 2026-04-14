from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import check_resource_ownership, get_owner_filter, require_admin
from app.db.session import get_db
from app.models.category import Category
from app.models.user import User
from app.schemas.admin import CategoryCreateAdmin, CategoryUpdateAdmin

router = APIRouter()


async def get_category_or_404(category_id: int, db: AsyncSession) -> Category:
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    return category


@router.get("")
async def list_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    owner_filter = get_owner_filter(current_user)
    query = select(Category)
    if owner_filter is not None:
        query = query.where(Category.owner_id == owner_filter)
    query = query.order_by(Category.sort_order, Category.id)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("")
async def create_category(
    body: CategoryCreateAdmin,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    category = Category(
        owner_id=current_user.id,
        name_uz=body.name_uz,
        name_ru=body.name_ru,
        image_url=body.image_url,
        sort_order=body.sort_order,
        is_active=body.is_active,
    )
    db.add(category)
    await db.flush()
    await db.refresh(category)
    return category


@router.get("/{category_id}")
async def get_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    category = await get_category_or_404(category_id, db)
    check_resource_ownership(category.owner_id, current_user)
    return category


@router.put("/{category_id}")
async def update_category(
    category_id: int,
    body: CategoryUpdateAdmin,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    category = await get_category_or_404(category_id, db)
    check_resource_ownership(category.owner_id, current_user)

    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(category, key, value)
    await db.flush()
    await db.refresh(category)
    return category


@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    category = await get_category_or_404(category_id, db)
    check_resource_ownership(category.owner_id, current_user)
    db.delete(category)
    await db.flush()
    return {"success": True}
